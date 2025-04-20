import json
import argparse


def enter_cmd_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file', metavar='file containing list of feats file', help='input filename which contains list of feats files', required=True)
	parser.add_argument('--type', metavar='type of traffc', help='type of traffic <eg.0(normal)/1(proxy)/2(all)>', required=True)
	parser.add_argument('--suffix', metavar='suffix of output file', help='input the suffix of output filename', required=False)
	args = parser.parse_args()
	return args

def main():
	args = enter_cmd_args()
	types = ['normal', 'proxy']
	suffix = ''
	if args.suffix:
		suffix = '_'+arg.suffix
	if int(args.type) == 2:
		rds = types
	else:
		rds = [types[int(args.type)]]
	with open(args.file, 'r') as f:
		files = f.readlines()
		f.close()
		files = [name.strip().replace('\n', '') for name in files]
	for rd in rds:
		new_dict = None
		for idx, name in enumerate(files):
			path = './'+name+'_'+rd+'.json'
			f = open(path, 'r')
			curr_dict = json.load(f)
			if idx == 0:
				new_dict = curr_dict.copy()
			else:
				new_dict.update(curr_dict)
			f.close()
		print(len(new_dict))
		out_path = 'feats_merged_'+rd+suffix+'.json'
		out_f = open(out_path, 'w')
		json.dump(new_dict, out_f)
		out_f.close()

if __name__ == "__main__":
	main()
