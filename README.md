# WaveFunctionCollapse Level Generation
An example of using the WaveFunctionCollapse algorithm to generate levels

This example is written in Python, and should work for any Python version. 

To run the code take the following steps: 

1. Download and install Python
2. Install the packages listed in the `requirements.txt` file
    - If you have pip installed, this can be done by running the `pip install -r requirements.txt` command in your terminal
3. Running `python WFC_train.py` will train a `colors` generation model based on the example in Chapter 5.
    - In `WFC_train.py` you will find a set of command line arguments that can be passed to change how the model is trained.
    - You can control, the domain (`colors`, `SMB`, or `LR`), as well as the learned pattern dimensions and pattern offsets
    - The arguments and their default values are  described in the file towards the bottom where they are defined
4. Running `python WFC_generate.py`, will try to generate a new 20x20 `colors` image. The generationn process (the Observe and Propagate loop) will be printed to the terminal so you can watch it try to generate. The final level (if successful) will be saved to the `Output` folder as an image and a text file. (Warning: this will overwrite any previous generated levels if new names are not chosen)
    - In `WFC_generate.py` you will find a set of command line arguments that can be passed to change how the image/level is generated.
    - You can control the domain, the trained model to use, the output dimensions, how many images/levels to generate, and the output name for the files
    - The arguments and their default values are  described in the file towards the bottom where they are defined


After this, you can experiment with the code and try the different included domains (Mario, Lode Runner, and a simple color example) by passing differen arguments to either scripts. You can also experiment with using different amounts of training levels (though the more data provided the slower the training and generation runs).

You can also try new domains by creating training examples and updating the argument definitions as needed!