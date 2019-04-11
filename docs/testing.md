## How to test Cartography as a developer

### Running from source

1. Follow steps 1 and 2 in [Installation](https://github.com/lyft/cartography/blob/master/README.md#installation).  Ensure that Neo4j Community is running on your local machine.
2. Run `cd {path-where-you-want-your-source-code}`.  Get the source code with `git clone git://github.com/lyft/cartography.git`
3. Run `cd cartography` and then `pip install .` (yes, actually type the period into the command line) to install Cartography from source.  
 
    ℹ️You may find it beneficial to use Python [virtualenvs](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) (or the  [virutalenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html#managing-environments)) so that packages installed via `pip` are easier to manage.

4. After this finishes you should be able to run Cartography from source with `cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>`.  Any changes to the source code in `{path-where-you-want-your-source-code}/cartography` are now locally testable by running `cartography` from the command line.

### Manually testing individual intel modules

After completing the section above, you are now able to manually test intel modules.
   
1. **If needed, comment out unnecessary lines** 

    See `cartography.intel.aws._sync_one_account()`[here](https://github.com/lyft/cartography/blob/master/cartography/intel/aws/__init__.py).  This function syncs different AWS objects with your Neo4j instance.  Comment out the lines that you don't want to test for.
  
    For example, IAM can take a long time to ingest so if you're testing an intel module that doesn't require IAM nodes to already exist in the graph, then you can comment out all of the `iam.sync_*` lines.
  
2. Save your changes and run `cartography` from a terminal as you normally would.

### Automated testing

1. TBD 🤭
