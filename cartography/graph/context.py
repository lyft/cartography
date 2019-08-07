"""

The general idea of this module is to provide objects with well-documented fields
that can be passed between different parts of the sync job and used to get parameters
for job queries. Example: you may pass a context in to the AWS sync module so that
that module can access the update_tag field as it needs to. The context class can
also be subclassed to allow module-specific context to be made available in the
same way.

Example:

    class ExampleContext(Context):
        def __init__(self, update_tag, example_field):
            Context.__init__(self, update_tag)
            self.example_field = example_field

        @classmethod
        def from_context(cls, context, example_field):
            return cls(context.update_tag, example_field)


    def sync_example(ctx):
        ctx = ExampleContext.from_context(ctx, example_field="example")
        # do whatever, accessing ctx.update_tag and ctx.example_field as needed
        return


    def sync_all(update_tag):
        ctx = Context(update_tag)
        sync_example(ctx)

"""


class Context:
    def __init__(self, update_tag):
        self.update_tag = update_tag

    def _to_dict(self):
        return {k.upper(): v for k, v in self.__dict__.items()}
