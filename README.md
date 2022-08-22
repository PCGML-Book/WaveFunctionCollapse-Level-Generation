# WaveFunctionCollapse Level Generation
An example of using the WaveFunctionCollapse algorithm to generate levels

This example is written in Python, and should work for any Python version. 

To run the code take the following steps: 

1. Download and install Python
2. Install the packages listed in the `requirements.txt` file
    - If you have pip installed, this can be done by running the `pip install -r requirements.txt` command in your terminal
3. Running `python WFC_train.py` will train a Lode Runner level generation model using 2 random levels from levels present in the LR_Data folder
4. Running `python WFC_generate.py`, will try to generate a new Lode Runner level in a tile representation. The generationn process (the Observe and Propagate loop) will be printed to the terminal so you can watch it try to generate. The final level (if successful) will be saved to `output/generated.txt` (Warning: this will overwrite any previous generated levels)


After this, you can experiment with the code and try the different included domains (Mario, Lode Runner, and a simple color example) by simply changing the `domain` variable value in the main function of both scripts. You can also experiment with using different amounts of training levels (though the more data provided the slower the training and generation runs).
