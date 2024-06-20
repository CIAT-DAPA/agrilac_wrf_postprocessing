import argparse

from .extract_data import extract_data

def main():

    parser = argparse.ArgumentParser(description="Resampling script")

    parser.add_argument("-i", "--inputs", help="Inputs path", required=True)
    parser.add_argument("-o", "--outputs", help="Outputs path", required=True)


    args = parser.parse_args()

    print("Reading inputs")
    print(args)

    input_path = args.inputs
    output_path = args.outputs
    
    postp = extract_data(input_path, output_path)

if __name__ == "__main__":
    main()