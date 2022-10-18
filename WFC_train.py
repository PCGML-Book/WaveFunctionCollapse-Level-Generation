import sys
import os
import glob
import pickle
import random
import argparse


# This corresponds to the WFC color example in Chapter 5
# You can change this example, or the arguments set at
# the bottom of the file for this domain to play with
# how the domain is modeled (e.g., size of the patterns)
def load_colors_domain():
	examples = [[
		['W', 'W', 'W', 'W'],
		['W', 'B', 'B', 'B'],
		['W', 'B', 'R', 'B'],
		['W', 'B', 'B', 'B']]]
	return examples

def load_examples(paths, subset=None):
	examples = []

	for path in paths:
		for levelFile in glob.glob(path):
			with open(levelFile) as fp:
				level = []
				for line in fp:
					row = []
					for cell in line:
						if cell not in ['\n', '\t', '\r']:
							row.append(cell)
					level.append(row)
				
				examples.append(level)

	if isinstance(subset, int) and subset < len(examples):
		examples = random.choices(examples, k=subset)

	return examples

# Find all the pattern_height X pattern_width size patterns in the examples
# Assumes an overlapping model
def extract_patterns(examples, pattern_height, pattern_width, row_offset=1, 
												col_offset=1, wrapping=False):
	extracted_patterns = []

	for example in examples:

		ex_height = len(example)
		ex_width = len(example[0])

		# each position will visited yield a pattern
		for row_index in range(0, ex_height, row_offset):
			for col_index in range(0, ex_width, col_offset):
				
				# if not using the wrapping version, then skip any positions
				# that extend beyond the edge of the example
				if not wrapping and \
						(col_index + pattern_width > ex_width or \
						row_index + pattern_height > ex_height):
					continue

				current_pattern = [
					[example[(row_index+j)%ex_height][(col_index+i)%ex_width] 
												for i in range(pattern_width)] 
												for j in range(pattern_height)]

				extracted_patterns.append(current_pattern)

	return extracted_patterns


# Count how many times each pattern appears in the training examples
# This is used when selecting a pattern/collapsing a position
def compute_pattern_occurrences(observed_patterns):

	pattern_counts = {}
	for pattern in observed_patterns:
		pattern_as_tuple = pattern_to_tuple(pattern)

		if pattern_as_tuple in pattern_counts:
			pattern_counts[pattern_as_tuple] += 1
		else:
			pattern_counts[pattern_as_tuple] = 1
	
	return pattern_counts

# used to convert the pattern 2d lists to tuples to make dict usage 
# and comparisons between patterns easier
def pattern_to_tuple(pattern):
	flattened_pattern = [tile for row in pattern for tile in row]
	pattern_as_tuple = tuple(flattened_pattern)

	return pattern_as_tuple

# given the observed patterns, get the unique patterns
def get_unique_patterns(observed_patterns):
	unique_patterns = []
	for pattern in observed_patterns:
		if pattern not in unique_patterns:
			unique_patterns.append(pattern)

	return unique_patterns

# determine the allowed adjacencies between the observed patterns
def compute_adjacencies(observed_patterns, row_offset=1, col_offset=1):
	adjacencies = {}

	for pattern_1 in observed_patterns:
		pattern_key = pattern_to_tuple(pattern_1)
		adjacencies[pattern_key] = {"above":[], "below":[], 
									"left":[], "right":[]}
		for pattern_2 in observed_patterns:
			pattern_value = pattern_to_tuple(pattern_2)
			# if pattern_key == str(pattern_value):
			# 	continue
			# check for allowed relative placements
			allowed_adjacencies = compute_adjacency_for_pattern_pair(pattern_1,
																	pattern_2,
																	row_offset,
																	col_offset)
			for direction in allowed_adjacencies:
				adjacencies[pattern_key][direction].append(pattern_value)

	return adjacencies

# for a given pair of patterns, determine any adjacencies allowed between them
def compute_adjacency_for_pattern_pair(p_1, p_2, row_offset, col_offset):

	height = len(p_1)
	width = len(p_1[0])
	
	p_1_top, p_1_bottom, p_1_left, p_1_right = get_pattern_slices(p_1, 
																row_offset, 
																col_offset)

	p_2_top, p_2_bottom, p_2_left, p_2_right = get_pattern_slices(p_2, 
																row_offset, 
																col_offset)


	allowed_adjacency_directions = []
	# check p_1
	#		 |
	#		 v 
	#		p_2
	if p_1_bottom == p_2_top:
		allowed_adjacency_directions.append("below")

	# check p_2
	#		 ^
	#		 |
	#		p_1
	if p_1_top == p_2_bottom:
		allowed_adjacency_directions.append("above")

	# check p_1 -> p_2
	if p_1_right == p_2_left:
		allowed_adjacency_directions.append("right")


	# check p_2 <- p_1 
	if p_1_left == p_2_right:
		allowed_adjacency_directions.append("left")

	return allowed_adjacency_directions

# helper function for the 'compute_adjacency_for_pattern_pair' which gets the
# sections of the provided pattern which are used to determine overlap/adjacency
# This essentially, gets the partial pieces of a given pattern to be used
# for determining which patterns can overlap in which ways
# e.g., we get the top portion of the pattern (as determined by the offsets)
# and then we can check for other patterns  if the top of pattern A is the same
# as the bottom of pattern B. Which tells us which patterns can be placed next
# to each other.
# This function just computes the partial pattern chunks, and the function
# above does the computing of which adjacencies are allowed
def get_pattern_slices(pattern, row_offset, col_offset):
	height = len(pattern)
	width = len(pattern[0])

	p_top, p_bottom = ([[None for c in range(width)] 
										for r in range(height-row_offset)] 
															for i in range(2))
	p_left, p_right = ([[None for c in range(width-col_offset)] 
										for r in range(height)] 
															for i in range(2))

	
	for row_index in range(height):
		for col_index in range(width):
			if row_index < height - row_offset:
				p_top[row_index][col_index] = pattern[row_index][col_index]

			if row_index >= row_offset:
				p_bottom[row_index-row_offset][col_index] = \
												pattern[row_index][col_index]

			if col_index < width - col_offset:
				p_left[row_index][col_index] = pattern[row_index][col_index]

			if col_index >= col_offset:
				p_right[row_index][col_index-col_offset] = \
												pattern[row_index][col_index]

	return p_top, p_bottom, p_left, p_right


if __name__ == '__main__':


	parser = argparse.ArgumentParser(
						description='Parameters for training the WFC model.')
	parser.add_argument('--domain',
						type=str, 
						default="colors",
	                    help='A string indicating which domain to use for ' +
	                    	'training. Possible values = ["colors", "LR","SMB"]. ' +
	                    	'Defaults to "colors"')
	parser.add_argument('--wrapping', 
						action='store_true',
						dest="wrapping",
						default=None,
	                    help='A flag indicating if the examples should be ' +
	                    	'assumed to wrap around  when training the model. ' +
	                    	'defaults set based on domain if this is not set ' +
	                    	'and the "not-wrapping" flag is not set.')
	parser.add_argument('--not_wrapping', 
						action='store_false',
						dest="wrapping",
						default=None,
	                    help='A flag indicating if the examples should be ' +
	                    	'assumed to wrap around  when training the model. ' +
	                    	'defaults set based on domain if this is not set ' +
	                    	'and the "wrapping" flag is not set.')
	parser.add_argument('--pattern_width', 
						type=int,
						help='An integer indicating the width of the ' +
							'pattern used by the WFC algorithm. Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--pattern_height', 
						type=int,
						help='An integer indicating the height of the ' +
							'pattern used by the WFC algorithm. Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--row_offset', 
						type=int,
						help='An integer indicating the row offset used '+
							'by the WFC algorithm between patterns. Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--col_offset', 
						type=int,
						help='An integer indicating the column offset of the ' +
							'by the WFC algorithm between patterns. Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--num_examples', 
						type=int,
						help='An integer indicating the how many examples to '+
							'load for the given domain. Ignored in the "colors" '+
							'domain. Default values used for other domains if '+
							'not passed. Note that only 1-2 levels are used by '+
							'default, because the time to train and generate '+
							'increases a lot based on example size.')

	parser.add_argument('--model_name',
						type=str, 
	                    help='A string indicating what name to give the trained '+ 
	                    	'model. e.g., "super_cool_WFC_model". Note that the '+ 
	                    	'file extension will be added automatically. Also ' +
	                    	'if none is provided will default to '+
	                    	'"trained_WFC_<domain>"')



	args = vars(parser.parse_args())

	# Remove None values from dictionary to ease checking later
	args = {key:value for key,value in args.items() if value is not None}


	domain = args["domain"]
	model_name = args.get("model_name", f"trained_WFC_{domain}")

	if domain == "SMB":
		wrapping = args.get("wrapping", False)
		pattern_height = args.get("pattern_height", 3)
		pattern_width = args.get("pattern_width", 3)
		row_offset = args.get("row_offset", 1)
		col_offset = args.get("col_offset", 1)
		num_examples = args.get("num_examples", 2)
		paths = ["./SMB1_Data/Processed/*.txt",
				"./SMB2_Data/Processed/*.txt"]
		
		examples = load_examples(paths, subset=num_examples)

	elif domain == "LR":
		wrapping = args.get("wrapping", True)
		pattern_height = args.get("pattern_height", 2)
		pattern_width = args.get("pattern_width", 2)
		row_offset = args.get("row_offset", 1)
		col_offset = args.get("col_offset", 1)
		num_examples = args.get("num_examples", 2)
		paths = ["./LR_Data/Processed/*.txt"]

		examples = load_examples(paths, subset=num_examples)

	elif domain == "colors":
		wrapping = args.get("wrapping", True)
		pattern_height = args.get("pattern_height", 2)
		pattern_width = args.get("pattern_width", 2)
		row_offset = args.get("row_offset", 1)
		col_offset = args.get("col_offset", 1)
		
		examples = load_colors_domain()

	else:
		print(f"'domain' must take a value from ['colors', 'LR', 'SMB'], "+
			"but {domain} was given.")
		exit()

	all_patterns = extract_patterns(examples, pattern_height, pattern_width, 
									row_offset=row_offset, col_offset=col_offset, 
																wrapping=wrapping)

	pattern_occurrences = compute_pattern_occurrences(all_patterns)

	unique_patterns = get_unique_patterns(all_patterns)

	learned_adjacencies = compute_adjacencies(unique_patterns, 
												row_offset=row_offset, 
												col_offset=col_offset)

	trained_WFC_model = {
					"domain": domain,
					"pattern_height":pattern_height,
					"pattern_width":pattern_width,
					"row_offset":row_offset,
					"col_offset":col_offset,
					"allowed_adjacencies": learned_adjacencies,
					"pattern_counts": pattern_occurrences
					}

	pickle.dump(trained_WFC_model, open(f"{model_name}.pickle", "wb"))
