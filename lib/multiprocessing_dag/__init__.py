# MIT License
#
# Copyright (c) 2019 Evan Davis
# Copyright (c) 2017 Mara contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import multiprocessing
import time


# This library was originally written by @ecdavis, who was inspired by https://github.com/mara/data-integration.
# Some helpful ways to understand the object model:
# - Pipelines and Tasks are both subclasses of Node.
# - A Pipeline is a parent of one or more Tasks, and a Task is a parent of one or more Commands.
# - If Node B is dependent on Node A completing its Commands successfully, we say that "Node A is **upstream** of Node
# B" and "Node B is **downstream** of Node A".

logger = logging.getLogger(__name__)

DEFAULT_PROCESS_LIMIT = 4  # TODO get core count?


class BaseCommand:
    def __init__(self):
        self.parent = None

    def run(self):
        raise NotImplementedError()


class Node:
    """
    Represents a node in a Directed Acyclic Graph.

    Args:
        name: The name of the node

    Members:
        parent: a reference to the parent of this Node.
        upstreams: Set of Nodes that this Node relies on
        downstreams: Set of Nodes that rely on this Node

    Examples:
        Not meant to be used directly. This is a base for Task and Pipeline.
    """
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.upstreams = set()
        self.downstreams = set()

    def parents(self):
        """
        :return: A list containing this node and all of its ancestors, if any.
        Example output: [ ... , grandparent, parent, self]
        """
        if self.parent:
            return self.parent.parents() + [self]
        else:
            return [self]

    def path(self):
        """
        :return: Same as `parents()`, except return a list of node names.
        Example output: [ ... , grandparent.name, parent.name, self.name]
        """
        return [node.name for node in self.parents()]

    def uri(self):
        """
        :return: Same as `path()`, except format the family line as a URI.
        Example output: ".../grandparent.name/parent.name/self.name"
        """
        return '/'.join(self.path())


class Task(Node):
    """
    A Task contains a list of Commands.

    Args:
        name: the name of the Task
        commands: a list of objects that implement the BaseCommand interface. Default: None.

    Members:
        Same as Node (by inheritance), and...
        commands: a list of objects that implement the BaseCommand interface.
    """
    def __init__(self, name, commands=None):
        super().__init__(name)

        self.commands = []
        for command in commands or []:
            self.add_command(command)

    def add_command(self, command):
        """
        Set this Task as the parent of the Command and add it to the `commands` list.
        :param command: The Command to add.
        """
        command.parent = self
        self.commands.append(command)

    def run(self):
        """
        Execute the `run()` function of each Command in this Task.
        :return: False if the command fails, else True.
        """
        for command in self.commands:
            if not command.run():
                return False
        return True


class Pipeline(Node):
    """
    A Pipeline is a collection of Nodes. A Pipeline itself is also a Node.

    Args:
        name: The name of the pipeline

    Members:
        Same as Node (via inheritance), and...
        nodes: a dict mapping node names to Node objects.
    """
    def __init__(self, name):
        super().__init__(name)

        self.nodes = {}

    def add(self, node, upstreams=None):
        """
        Add a Node to the Pipeline. Optionally include a list of upstream dependencies.
        :param node: The Node
        :param upstreams: A list of Pipelines that this Pipeline relies on. If any of these fail, this Pipeline won't run.
        Default: None.

        Example:
            ```
            pipeline_main = multiprocessing_dag.Pipeline(name='main')
            pipeline_main.add(pipeline_subjob, upstreams=[pipeline_init])
            ```
            means that pipeline_init must execute successfully before pipeline_subjob can start.
        """
        if node.name in self.nodes:
            raise ValueError(f'A node named "{node.name}"" already exists in pipeline {self.name}.')

        node.parent = self
        self.nodes[node.name] = node

        for upstream in upstreams or []:
            self.add_dependency(upstream, node)

    def add_dependency(self, upstream, downstream):
        """
        Add a Pipeline dependency relationship.
        :param upstream: The Pipeline that is an upstream dependency of this Pipeline
        :param downstream: The Pipeline that is downstream of this Pipeline
        :return:
        """
        upstream.downstreams.add(downstream)
        downstream.upstreams.add(upstream)


class Process(multiprocessing.Process):
    """
    Subclass of multiprocessing.Process: adds logging and a status_queue.
    Params:
        task: Task object
        status_queue: a multiprocessing.Queue object.
    """
    def __init__(self, task, status_queue):
        super().__init__(name=f"task-{task.uri()}")  # TODO don't use uri

        self.task = task
        self.status_queue = status_queue
        self.logger = logging.getLogger(task.uri())  # TODO uri?

    def run(self):
        success = True
        try:
            result = self.task.run()
            if not result:
                self.logger.warning(f"Command failure in task '{self.task.uri()}'.")
                success = False
        except Exception:  # TODO let KeyboardInterrupt and others bubble up
            self.logger.exception(f"Unhandled exception in task '{self.task.uri()}'.")
            success = False
        self.status_queue.put(success)
        self.status_queue.close()


class Runner:
    def __init__(self, process_limit=DEFAULT_PROCESS_LIMIT):  # TODO set default value like this or do lookup?
        self.process_limit = process_limit
        self.queued_nodes = []
        self.finished_nodes = set()
        self.running_pipelines = set()
        self.failed_pipelines = set()
        self.running_tasks = {}

    def _dequeue(self):
        """
        Returns next node in the queue without upstreams or where all upstreams have been run already.
        """
        for node in self.queued_nodes:
            if not node.upstreams or node.upstreams.issubset(self.finished_nodes):
                self.queued_nodes.remove(node)
                if node.parent in self.failed_pipelines:
                    self.finished_nodes.add(node)
                else:
                    return node
        return None

    def _enqueue_pipeline(self, pipeline):
        """
        Add all nodes of a pipeline to the Runner's queue.
        :param pipeline: The pipeline to enqueue
        """
        # Connect pipeline nodes without upstreams to upstreams of pipeline
        for upstream in pipeline.upstreams:
            for sub_node in pipeline.nodes.values():
                if not sub_node.upstreams:
                    pipeline.add_dependency(upstream, sub_node)
        # Connect pipeline nodes without downstreams to downstream of pipeline
        for downstream in pipeline.downstreams:
            for sub_node in pipeline.nodes.values():
                if not sub_node.downstreams:
                    pipeline.add_dependency(sub_node, downstream)
        self.running_pipelines.add(pipeline)
        for sub_node in pipeline.nodes.values():
            self.queued_nodes.append(sub_node)

    def _start_task(self, task):
        """
        Run the given Task in a Process object. Create a status_queue to record the statuses of the Task's Commands.
        :param task: The Task to run
        :return: the Process object
        """
        status_queue = multiprocessing.Queue()
        task_process = Process(task, status_queue)
        task_process.start()
        return task_process

    def _finish_tasks(self):
        """
        Calls multiprocessing.Process.join() on completed Tasks.
        Keeps track of failed_pipelines, finished_nodes, and running_tasks.
        """
        for running_process in list(self.running_tasks.values()):
            # NOTE tests indicated that is_alive could sometimes return true even when process execution had been
            # NOTE completed, so we also check the status queue even though that's documented as being unreliable
            # NOTE further testing needed here, I think
            if running_process.is_alive() and running_process.status_queue.empty():
                continue
            logger.info(f"Finishing task '{running_process.task.uri()}'.")
            del self.running_tasks[running_process.task]
            self.finished_nodes.add(running_process.task)
            exit_code = running_process.exitcode
            status_result = running_process.status_queue.get()
            if exit_code is None:
                logger.info(f"Joining task '{running_process.task.uri()}'.")
                running_process.join()  # TODO danger! no timeout!
                exit_code = running_process.exitcode
            failed = exit_code != 0 or not status_result
            if failed:
                logger.warning(f"Failed task '{running_process.task.uri()}'.")
                for parent in running_process.task.parents()[:-1]:
                    logger.warning(f"Failing pipeline '{parent.uri()}'.")
                    self.failed_pipelines.add(parent)

    def _finish_pipelines(self):
        """
        Perform bookkeeping of running and finished pipelines.
        """
        for running_pipeline in list(self.running_pipelines):
            if set(running_pipeline.nodes.values()).issubset(self.finished_nodes):
                logger.info(f"Finishing pipeline '{running_pipeline.uri()}'.")
                # failed = (running_pipeline in self.failed_pipelines)  # TODO
                self.running_pipelines.remove(running_pipeline)
                self.finished_nodes.add(running_pipeline)

    def run(self, pipeline):
        """
        Run the given pipeline by adding it to the Runner's queue and executing each sub node.
        """
        self.queued_nodes.append(pipeline)

        while self.queued_nodes or self.running_tasks:
            if len(self.running_tasks) < self.process_limit:
                next_node = self._dequeue()
                if isinstance(next_node, Pipeline):
                    logger.info(f"Starting pipeline '{next_node.uri()}'.")
                    self._enqueue_pipeline(next_node)
                elif isinstance(next_node, Task):
                    logger.info(f"Starting task '{next_node.uri()}'.")
                    node_process = self._start_task(next_node)
                    self.running_tasks[next_node] = node_process
                else:
                    pass  # NOTE happens when we dequeue None
            self._finish_tasks()
            self._finish_pipelines()
            time.sleep(0.001)

        self._finish_pipelines()
