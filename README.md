# NLP_Projects

HMM folder contains a HMM model for POS tagging <br/>

LSTM folder contains a CNN-LSTM model for POS tagging <br/>

To train, run the following line on command line <br/>
python buildtagger.py sents.train model-file

To test, run the following line on command line <br/>
python runtagger.py sents.test model-file sents.out

To evaluate, run the following line on command line <br/>
python eval.py sents.out sents.answer
<br/>
HMM model has an accuracy of 93.4% <br/>
CNN-LSTM model has accuracy of 94.8% if trained under 10 mins on a CPU. <br/>
If training time increases, or run on a GPU, CNN-LSTM model can have an accuracy of >98%.
