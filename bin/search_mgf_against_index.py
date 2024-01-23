import argparse
import matchms
import requests
import csv
from tqdm import tqdm
import json

"""
Example URL:
https://fasst.gnps2.org/search?usi=None&library=gnpslibrary&query_spectrum={%22n_peaks%22:15,%22peaks%22:[[165.06979370117188,0.38009798526763916],[167.072998046875,1.7413330078125],[179.07260131835938,0.2999509871006012],[180.08079528808594,100.0],[181.08859252929688,2.8455820083618164],[182.09649658203125,23.914995193481445],[192.08079528808594,0.6896359920501709],[193.0886993408203,0.2419929951429367],[208.07569885253906,3.9236950874328613],[210.09129333496094,51.83255386352539],[236.0706024169922,4.025279998779297],[253.09719848632812,21.652437210083008],[254.08120727539062,46.069068908691406],[255.0872039794922,0.3038550019264221],[271.1077880859375,0.7285820245742798]],%22precursor_charge%22:0,%22precursor_mz%22:271.1077}
"""

def build_url(spectrum, args):
    search_index = args.search_index
    
    spectrum_dict=spectrum.to_dict()
    peaks_json = spectrum_dict['peaks_json']
    spectrum_dict = {'precursor_mz': spectrum_dict['precursor_mz'], 'peaks':peaks_json, 'charge': spectrum_dict['charge']}
    base_url = 'https://fasst.gnps2.org/search'
    
    query_spectrum = {
        'peaks': peaks_json,
        'precursor_charge': spectrum_dict['charge'],
        'precursor_mz': spectrum_dict['precursor_mz'],
    }
    query_spectrum_json = json.dumps(query_spectrum)
    data = {
        'library': args.search_index,
        'analog': 'Yes' if args.analog else 'No',
        'cache': 'No' if args.no_cache else 'Yes',
        'lower_delta': args.lower_delta,
        'upper_delta': args.upper_delta,
        'pm_tolerance': args.pm_tolerance,
        'fragment_tolerance': args.fragment_tolerance,
        'cosine_threshold': args.cosine_threshold,
        'query_spectrum': query_spectrum_json,
    }

    return {'url': base_url ,'data': data}
    

def main():
    parser = argparse.ArgumentParser(description='Search MGF against index')
    parser.add_argument('--input_mgf', type=str, help='Input MGF file')
    parser.add_argument('--search_index', type=str, help='Search index')
    parser.add_argument('--output', type=str, help='Output file')
    parser.add_argument('--analog', type=bool, default=False, help='Search analogs')
    parser.add_argument('--no_cache', type=bool, default=False, help='Do not use cache')
    parser.add_argument('--lower_delta', type=float, default=130, help='Lower delta mass')
    parser.add_argument('--upper_delta', type=float, default=200, help='Upper delta mass')
    parser.add_argument('--pm_tolerance', type=float, default=0.05, help='Precursor mass tolerance')
    parser.add_argument('--fragment_tolerance', type=float, default=0.05, help='Fragment mass tolerance')
    parser.add_argument('--cosine_threshold', type=float, default=0.7, help='Cosine threshold')
                        
    args = parser.parse_args()
    
    # Print all arguments
    print("Input arguments:")
    for arg in vars(args):
        print(arg, getattr(args, arg))
    
    spectra = matchms.importing.load_from_mgf(args.input_mgf)  
    
    print("Preparring URLs")
    queries = [build_url(x, args) for x in tqdm(spectra)]
    
    print("Searching and writing results")
    with open(args.output, 'w') as output_file:
        csvdictwriter = csv.DictWriter(output_file, fieldnames=['query_index', 'delta_mass', 'matching_USI', 'matching_charge', 'matching_cosine', 'matching_peaks',])
        csvdictwriter.writeheader()
        
        # For each url, try to get the reponse, retrying 3 times  
        for query_index, query in enumerate(tqdm(queries)):
            for _ in range(3):
                try:
                    response = requests.post(query['url'], data=query['data'])
                    if response.status_code == 200:
                        json_response = response.json()
                        for match in json_response['results']:
                            csvdictwriter.writerow({'query_index': query_index, 'delta_mass': match['Delta Mass'], 'matching_USI': match['USI'], 'matching_charge': match['Charge'], 'matching_cosine': match['Cosine'], 'matching_peaks': match['Matching Peaks']})
                        break
                    else:
                        continue
                    
                except Exception as e:
                    print(e)
                    print("Retrying")
                
    
if __name__ == "__main__":
    main()