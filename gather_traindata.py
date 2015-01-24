def main(column):
    """
    Interactive way to gather hand-labeled data for sentiment scoring (1-5 stars) as well as static aspect identification.

    name - column to be labeling {'sentiment'|'category'}

    ex. $ python gather_traindata.py Kevin  # from bash shell
    ex. >>> main("column")    # from a python session
    """

    # Import necessary modules
    import pandas as pd


    # Get data from the training set.
    filename = 'data/train/review_sentences_mexican'
    try:
        sentences = pd.read_pickle(filename+'_full'+'.pkl')
    except:
        sentences = pd.read_pickle(filename+'.pkl')
        print "Begin labeling data!"

    # If there's no column by the name passed, add it
    if column not in sentences.columns:
        sentences[column] = 0


    # Add sentiment score 1 sentence at a time to the dataframe
    if column=='sentiment':

        # Loop through each element in the dataframe
        for ii in range(len(sentences)):
            if sentences[column].iloc[ii] < 1:
                print ii
                inputstring = sentences['text'].iloc[ii] + '\n --> '
                score = raw_input(inputstring)
                while ((score!='1') & (score!='2') & (score!='3') &
                       (score!='4') & (score!='5') & (score!='quit')):
                    print 'Please enter an integer 1-5  (or "quit") '
                    score = raw_input(inputstring)

                # If score = 'quit', break out of loops
                if score=='quit':
                    break    # break out of for loop

                # If score is entered properly, record it
                sentences.ix[ii,column] = int(score)


    if column=='category':

        # Loop through each element in the dataframe
        for ii in range(len(sentences)):
            if sentences[column].iloc[ii] < 1:
                score = raw_input(sentences['text'].iloc[ii])
                #while ((score!='1') & (score!='2') & (score!='3') &
                #       (score!='4') & (score!='5') & (score!='quit')):
                #    print 'Please enter an integer 1-5  (or "quit") '
                #    score = raw_input(sentences['text'].iloc[ii])
                #
                ## If score = 'quit', break out of loops
                #if score=='quit':
                #    break    # break out of for loop
                #
                ## If score is entered properly, record it
                #sentences[column].iloc[ii] = int(score)


    # Save pickle back to original filename
    sentences.to_pickle(filename+'_full'+'.pkl')



if __name__=="__main__":
    import sys
    main(sys.argv[1])
