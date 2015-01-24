#!/usr/bin/env python

"""
sentiment.py
########################################################################
#
#        Kevin Wecht                22 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    main.py
#        - Handles input from flask
#        - Calls necessary python routines to query database
#        - pushes results to website
#
#    EXAMPLE
#        
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import numpy as np
import pandas as pd
import sqlfuncs

########################################################################


def getrequest(string):
    """
    Receives request from the web input in the form of a string.

    string - string obtained from user input in the web interface.
    """

    # Error handling. (should be done in flask environment, prior to
    #     being passed to this function.

    # Perform mysql query(ies) and perform operations in python
    #     using the string provided.
    results = sqlfuncs.query_term(string)

    
