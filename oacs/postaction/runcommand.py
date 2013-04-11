#!/usr/bin/env python
# encoding: utf-8

## @package runcommand
#
# This contains a generic class to run any command

from oacs.postaction.basepostaction import BasePostAction

## RunCommand
#
# Run a generic command with variable substitution (you can access any scalar variable from Runner)
class RunCommand(BasePostAction):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BasePostAction.__init__(self, config, *args, **kwargs)

    ## Run a command
    # @param Playerinfo A dict containing the info of the last detected cheater
    # @param **kwargs(Any_Variable) Any other variable passed in argument will be substituted by its string representation
    def action(self, Playerinfo=None, *args, **kwargs):
        # Get the list of commands to run
        cmdlist = self.config.config.get('runcommand', None)
        # If this module is enabled but there's no command, quit
        if cmdlist is None: return None
        # If in fact we have only one command, we convert it to a list of one element
        if type(cmdlist) == type(str):
            cmdlist = [cmdlist]
        # Add the variables inside Playerinfo dict as variables themselves
        kwargs = kwargs.extend(Playerinfo)
        # For each command
        for cmd in cmdlist:
            # For each available variable
            for key, value in kwargs.iteritems:
                # Try to replace the variable by its value if it's in the command
                try:
                    cmd = cmd.replace("$%s" % key, str(value)) # replace all occurences of the variable key/name by its value (string representation of the value)
                # Error, we just pass
                except Exception, e:
                    print(e)
                    pass
            # Execute the command
            print(cmd)
            #os.execute(cmd)

        return True