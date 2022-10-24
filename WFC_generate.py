import json
import random
import math
import sys
import os
import glob
import pickle
import argparse

from PIL import Image
from sty import fg, bg, ef, rs, Style, RgbFg

def generate_new_level(height, width, model, wrapping=False, max_attempts = 5):
	
	pattern_occurrences = model["pattern_counts"]
	possible_patterns = list(pattern_occurrences.keys())
	allowed_adjacencies = model["allowed_adjacencies"]

	for key in allowed_adjacencies.keys():
		for direction in allowed_adjacencies[key].keys():
			allowed_adjacencies[key][direction] = [pattern_to_tuple(p) for p in allowed_adjacencies[key][direction]]

	domain = model["domain"]


	i=0
	while i < max_attempts:
		level = initialize_level(height, width, possible_patterns)

		possible_positions = get_observable_positions(level, pattern_occurrences)
		
		while len(possible_positions) > 0:
			pos, pat = observe(level, pattern_occurrences, possible_positions)

			level[pos[0]][pos[1]] = [pat]
			print_level_in_progress(level, domain)

			level = propagate(level, possible_patterns, allowed_adjacencies, 
												pattern_occurrences, wrapping)



			possible_positions = get_observable_positions(level, pattern_occurrences)
		
		if not is_valid_level(level):
			print(f"Contradiction reached during sampling. A position in the level "+
				"has 0 possible patterns. Generation attempt {i} failed.")
			i+=1
		else:
			break
			
	return finalize_level(level)

def initialize_level(height, width, possible_patterns):

	level = [[possible_patterns for column in range(width)]
									for row in range(height)]

	return level

# check if there are any positions with 0 options available
def is_valid_level(level):
	for row in level:
		for cell in row:
			if len(cell) == 0:
				return False

	return True

def pattern_to_tuple(pattern):
	flattened_pattern = [tile for row in pattern for tile in row]
	pattern_as_tuple = tuple(flattened_pattern)

	return pattern_as_tuple

def get_observable_positions(level, pattern_occurrences):
	# gather the positions with the fewest available options
	lowest_entropy = float("inf")
	possible_positions = []
	for row_index in range(len(level)):
		for col_index in range(len(level[row_index])):
			

			entropy = compute_shannon_entropy(level[row_index][col_index],
														pattern_occurrences)

			# either a fail state (no options), or a collapsed state (1 option)
			if entropy == 0:
				if len(level[row_index][col_index]) == 0:
					print("Ran into a fail case; no options available for a "+
						"position. Restarting generation.")
					return []
				else:
					# not a fail state, this position is just already collapsed
					continue
			# new lowest entropy position found, overwrite possible positions
			elif entropy < lowest_entropy:
				lowest_entropy = entropy
				possible_positions = [[row_index,col_index]]

			# position with the same as current lowest entropy,
			# append to possible positions
			elif entropy == lowest_entropy:
				possible_positions.append([row_index,col_index])
			
			# entropy is higher than current lowest entropy, skip position
			else:
				continue

	return possible_positions

def observe(level, pattern_occurrences, possible_positions):
	# randomly choose which position to collapse
	position = random.choice(possible_positions)
	
	# get the possible patterns at the chosen position
	possible_patterns_at_position = level[position[0]][position[1]]

	# construct a weighted choice for those patters based on occurrences
	weights = [pattern_occurrences[pattern_to_tuple(pattern)] 
								for pattern in possible_patterns_at_position]

	total_weight = sum(weights)
	weights=[weight/total_weight for weight in weights]

	chosen_pattern = random.choices(possible_patterns_at_position, 
									weights=weights, 
									k=1)[0]

	return position, chosen_pattern

def compute_shannon_entropy(patterns, occurrences):
	pattern_counts = [occurrences[pattern_to_tuple(pat)] for pat in patterns]
	
	total = sum(pattern_counts)
	pattern_counts = [count/total for count in pattern_counts]

	shannon_entropy = -sum([count*math.log(count) for count in pattern_counts])

	return shannon_entropy

# for every position, 
	#	get the patterns allowed at that position
	#	get the patterns allowed at surrounding positions given those patterns
	#	remove at patterns at the surrounding positions that are not allowed
	#	repeat this while any changes are made to the allowed patterns 
def propagate(level, patterns, allowed_adjacencies, pattern_occurrences, wrapping):
	still_updating = True
	i=0
	while still_updating:
		i+=1
		still_updating = False

		#get all positions sorted by entropy
		positions = [(r,c) for r in range(len(level)) 
										for c in range(len(level[0]))]

		sorted_positions = []
		for pos in positions:
			entropy = compute_shannon_entropy(level[pos[0]][pos[1]],
												pattern_occurrences)

			if len(sorted_positions) == 0:
				sorted_positions.append((pos,entropy))
			else:
				index = 0
				while index < len(sorted_positions) and \
										entropy > sorted_positions[index][1]:
					index += 1
				if index < len(sorted_positions):
					sorted_positions.insert(index, (pos,entropy))
				else:
					sorted_positions.append((pos,entropy))


		for pos,_ in sorted_positions:
			r = pos[0]
			c = pos[1]

			allowed_above = []
			if wrapping:
				current_allowed_above = {pattern_to_tuple(pat) for pat in level[(r-1)%len(level)][c]}
			elif not wrapping and r > 0:
				current_allowed_above = {pattern_to_tuple(pat) for pat in level[r-1][c]}
			# if not wrapping, assume anything can be placed out of bounds
			elif not wrapping and r <= 0:
				current_allowed_above = {pattern_to_tuple(pat) for pat in patterns}
			
			allowed_below = []
			if wrapping:
				current_allowed_below = {pattern_to_tuple(pat) for pat in level[(r+1)%len(level)][c]}
			elif not wrapping and r < len(level)-1:
				current_allowed_below = {pattern_to_tuple(pat) for pat in level[r+1][c]}
			# if not wrapping, assume anything can be placed out of bounds
			elif not wrapping and r >= len(level):
				current_allowed_below = {pattern_to_tuple(pat) for pat in patterns}

			allowed_left = []
			if wrapping:
				current_allowed_left = {pattern_to_tuple(pat) for pat in level[r][(c-1)%len(level[r])]}
			elif not wrapping and c > 0:
				current_allowed_left = {pattern_to_tuple(pat) for pat in level[r][c-1]}
			# if not wrapping, assume anything can be placed out of bounds
			elif not wrapping and c <= 0:
				current_allowed_left = {pattern_to_tuple(pat) for pat in patterns}

			allowed_right = []
			if wrapping:
				current_allowed_right = {pattern_to_tuple(pat) for pat in level[r][(c+1)%len(level[r])]}
			elif not wrapping and c < len(level[0])-1:
				current_allowed_right = {pattern_to_tuple(pat) for pat in level[r][c+1]}
			# if not wrapping, assume anything can be placed out of bounds
			elif not wrapping and c >= len(level[0]):
				current_allowed_right = {pattern_to_tuple(pat) for pat in patterns}
			
			allowed_above = {pattern_to_tuple(pat_above) for pat_curr in level[r][c] for pat_above in allowed_adjacencies[pattern_to_tuple(pat_curr)]["above"]}
			allowed_below = {pattern_to_tuple(pat_below) for pat_curr in level[r][c] for pat_below in allowed_adjacencies[pattern_to_tuple(pat_curr)]["below"]}
			allowed_left = {pattern_to_tuple(pat_left) for pat_curr in level[r][c] for pat_left in allowed_adjacencies[pattern_to_tuple(pat_curr)]["left"]}
			allowed_right = {pattern_to_tuple(pat_right) for pat_curr in level[r][c] for pat_right in allowed_adjacencies[pattern_to_tuple(pat_curr)]["right"]}

			if wrapping:
				level[(r-1)%len(level)][c] = list(allowed_above.intersection(current_allowed_above))
				level[(r+1)%len(level)][c] = list(allowed_below.intersection(current_allowed_below))
				level[r][(c-1)%len(level[r])] = list(allowed_left.intersection(current_allowed_left))
				level[r][(c+1)%len(level[r])] = list(allowed_right.intersection(current_allowed_right))

				if len(level[(r-1)%len(level)][c]) < len(current_allowed_above) or \
					len(level[(r+1)%len(level)][c]) < len(current_allowed_below) or \
					len(level[r][(c-1)%len(level[r])]) < len(current_allowed_left) or \
					len(level[r][(c+1)%len(level[r])]) < len(current_allowed_right):
					still_updating = True
			else:
				if r > 0:
					level[r-1][c] = list(allowed_above.intersection(current_allowed_above))
					if len(level[r-1][c]) < len(current_allowed_above):
						still_updating = True
				if r < len(level)-1:
					level[r+1][c] = list(allowed_below.intersection(current_allowed_below))
					if len(level[r+1][c]) < len(current_allowed_below):
						still_updating = True
				if c > 0:
					level[r][c-1] = list(allowed_left.intersection(current_allowed_left))
					if len(level[r][c-1]) < len(current_allowed_left):
						still_updating = True
				if c < len(level[0])-1:
					level[r][c+1] = list(allowed_right.intersection(current_allowed_right))
					if len(level[r][c+1]) < len(current_allowed_right):
						still_updating = True
		
	return level



def finalize_level(level):

	final_level = [[cell[0][0][0] for cell in row] for row in level]

	return final_level

def print_level_in_progress(level, domain):

	level_in_progress = [[cell[0][0][0] if len(cell) == 1 else len(cell) for cell in row] for row in level]

	if domain == "colors":
		for row in level_in_progress:
			for cell in row:
				if cell == 'W':
					color = fg.white
				elif cell == 'R':
					color = fg.red
				elif cell == 'B':
					color = fg.da_grey
				else:
					color = fg.da_yellow
				print(color + f"{cell}", end=" ")
			print("")
		print("")
		print(fg.rs+"")
	
	elif domain == "SMB":
		for row in level_in_progress:
			for cell in row:
				if cell in ["X", "S"]:
					color = fg.da_red
				elif cell == "-":
					color = fg.li_cyan
				elif cell in ["?", "Q"]:
					color = fg.yellow
				elif cell == "E":
					color = fg.red
				elif cell in ["<", ">", "[", "]"]:
					color = fg.green
				elif cell == "o":
					color = fg.li_yellow
				elif cell in ["B", "b"]:
					color = fg.da_grey
				else:
					color = fg.white
				print(color + f"{cell}", end=" ")
			print("")
		print("")
		print(fg.rs+"")
	elif domain == "LR":
		for row in level_in_progress:
			for cell in row:
				if cell == "B":
					color = fg.da_red
				elif cell == "b":
					color = fg.red
				elif cell == ".":
					color = fg.da_grey
				elif cell == "-":
					color = fg.white
				elif cell == "#":
					color = fg.white
				elif cell == "G":
					color = fg.yellow
				elif cell == "E":
					color = fg.li_magenta
				elif cell == "M":
					color = fg.li_cyan
				else:
					color = fg.da_yellow
				print(color + f"{cell}", end=" ")
			print("")
		print("")
		print(fg.rs+"")

	return level_in_progress

# Visualize a Generated Level
def visualize_level(level, sprite_mapping, sprites, background_color, level_name, level_number, domain):
	
	level_height = len(level)
	level_width = len(level[0])

	# sprites are max 18x18 pixels
	viz_height =  18*level_height
	viz_width =  18*level_width

	# this creates the image for the level
	image = Image.new("RGB", (viz_width, viz_height), color=background_color)
	pixels = image.load()#this loads the level image's pixels so we can edit them


	for y in range(0, level_height):
		for x in range(0, level_width):
			imageToUse = None
			if level[y][x] in sprite_mapping.keys():
				imageToUse = sprites[sprite_mapping[level[y][x]]]
			
			# Special handling to make SMB levels look nicer
			elif level[y][x]=="X" and domain == "SMB":
				#Rules about ensuring the right sprite is used
				if y==level_height-2:
					imageToUse = sprites["groundTop"]
				elif y==level_height-1:
					#Check if we have a solid tile above or not
					if level[y-1][x]=="X":
						imageToUse = sprites["groundBottom"]
					else:
						imageToUse = sprites["groundTop"]
				else:
					imageToUse = sprites["stair"]
			
			if not imageToUse == None:
				pixelsToUse = imageToUse.load()
				for x2 in range(0, 18):
					for y2 in range(0, 18):
						if pixelsToUse[x2,y2][3]>0:
							pixels[x*18+x2,y*18+y2] = pixelsToUse[x2,y2][0:-1]

	image.save(f'Output/{level_name}_{level_number}_viz.jpeg', "JPEG")

if __name__ == '__main__':


	parser = argparse.ArgumentParser(
						description='Parameters for training the WFC model.')
	parser.add_argument('--domain',
						type=str, 
						default="colors",
	                    help='A string indicating which domain to use for ' +
	                    	'training. Possible values = ["colors", "LR","SMB"]. ' +
	                    	'Defaults to "colors"')
	parser.add_argument('--model_name',
						type=str, 
	                    help='A string indicating the name of the trained model '+ 
	                    	'to load. e.g., "super_cool_WFC_model". Note that the '+ 
	                    	'file extension will be added automatically. Also ' +
	                    	'if none is provided will default to '+
	                    	'"trained_WFC_<domain>"')
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
	parser.add_argument('--level_height', 
						type=int,
						help='An integer indicating the height of the ' +
							'level to be generated Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--level_width', 
						type=int,
						help='An integer indicating the width of the ' +
							'level to be generated Defaults ' +
							'are set based on domain if not passed.')
	parser.add_argument('--num_levels', 
						type=int,
						default=1,
						help='An integer indicating the how many levels to '+
							'generate. Defaults to 1 if not passsed.')
	parser.add_argument('--level_name',
						type=str, 
	                    help='A string indicating the name to give the '+ 
	                    	'generated levels. e.g., "super_cool_level". Note ' +
	                    	'that the file extension and level number will be ' +
	                    	'added automatically. Also if none is provided will ' +
	                    	'default to "generated"')

	args = vars(parser.parse_args())

	# Remove None values from dictionary to ease checking later
	args = {key:value for key,value in args.items() if value is not None}

	domain = args["domain"]
	model_name = args.get("model_name", f"trained_WFC_{domain}")
	num_levels = args.get("num_levels", 1)
	level_name = args.get("level_name", f"generated")

	if domain == "SMB":
		wrapping = args.get("wrapping", False)
		level_height = args.get("level_height", 14)
		level_width = args.get("level_width", 16)
		sprite_mapping = {
				"S": "brick",
				"?": "exclamationBox",
				"Q": "exclamationBoxEmpty",
				"E": "enemy",
				"<": "bushTopLeft",
				">": "bushTopRight",
				"[": "bushLeft",
				"]": "bushRight",
				"o": "coin",
				"B": "arrowTop",
				"b": "arrowBottom"
			}
		background_color = (223, 245, 244)


	elif domain == "LR":
		wrapping = args.get("wrapping", True)
		level_height = args.get("level_height", 16)
		level_width = args.get("level_width", 16)
		sprite_mapping = {
				"B": "solid",
				"b": "diggable",
				"-": "branch",
				"#": "ladder",
				"E": "enemy",
				"M": "player",
				"G": "gem"
			}
		background_color = (223, 245, 244)

	elif domain == "colors":
		wrapping = args.get("wrapping", True)
		level_height = args.get("level_height", 20)
		level_width = args.get("level_width", 20)
		sprite_mapping = {
				"B": "black",
				"R": "red",
				"W": "white"
			}
		background_color = (123, 123, 123)

	else:
		print("'domain' must take a value from ['colors', 'LR', 'SMB'], "+
			f"but {domain} was given.")
		exit()

	trained_model = pickle.load(open(f"{model_name}.pickle", "rb"))
	if trained_model["domain"] != domain:
		print("trained model's domain must match the target domain")
		print(f"trained model: {trained_model['domain']}, target: {domain}")
		exit()

	#Load sprites
	sprites = {}
	for filename in glob.glob(f"./Sprites/{domain}/*.png"):
		im = Image.open(filename)
		name = filename.split("/")[-1].split(".")[0]
		sprites[name] = im.convert('RGBA')

	for level_number in range(num_levels):
		level = generate_new_level(level_height, level_width, trained_model, 
												wrapping=wrapping, max_attempts=5)

		print_level_in_progress(level, trained_model["domain"])

		with open(f'Output/{level_name}_{level_number}.txt', 'w') as output:
			for row in level:
				for cell in row:
					output.write(cell)
				output.write('\n')
		visualize_level(level, sprite_mapping, sprites, background_color, level_name, level_number, domain)
