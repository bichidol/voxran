import os
import random
import itertools
import argparse

def parse_notes_in_tracks(track_data):
    structured_notes = {track: [] for track in track_data.keys() if track not in ['TRACK1', 'TRACK8']}

    for track, notes in track_data.items():
        if track in ['TRACK1', 'TRACK8']:
            continue  

        for note_line in notes:
            note_info = note_line.split('\t') 
            if len(note_info) >= 3:
                timestamp, note_type, _ = note_info  
                structured_notes[track].append({
                    'timestamp': timestamp,
                    'type': 'chip' if note_type == '0' else 'hold', 
                })

            #print(f"Parsed {track} note: {note_info}")

    return structured_notes

def identify_chip_timestamps(structured_notes):
    chip_timestamps = {}
    relevant_tracks = [f'TRACK{i}' for i in range(2, 8)]

    for track in relevant_tracks:
        for note in structured_notes[track]:
            if note['type'] == 'chip':
                timestamp = note['timestamp']
                if timestamp in chip_timestamps:
                    chip_timestamps[timestamp] += 1  #increment the counter for this timestamp
                else:
                    chip_timestamps[timestamp] = 1  #initialize counter for this new timestamp

            #print(f"Processed note in {track}: {note}")

    sorted_chip_timestamps = dict(sorted(chip_timestamps.items()))

    return sorted_chip_timestamps

def identify_hold_timestamps(structured_notes):
    hold_timestamps = {}
    relevant_tracks = [f'TRACK{i}' for i in range(2, 8)]  #buttons through fx

    for track in relevant_tracks:
        for note in structured_notes[track]:
            if note['type'] == 'hold':  #holds
                timestamp = note['timestamp']
                if timestamp in hold_timestamps:
                    hold_timestamps[timestamp] += 1 
                else:
                    hold_timestamps[timestamp] = 1  

            #print(f"Processed hold in {track}: {note}")

    sorted_hold_timestamps = dict(sorted(hold_timestamps.items()))

    return sorted_hold_timestamps


def parse_beat_info(filepath):
    """
    Parses the BEAT INFO from a VOX file.

    :param filepath: Path to the VOX file.
    :return: List of dictionaries, each representing a time sig change.
    """
    beat_info = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
        
        in_beat_info = False
        for line in lines:
            line = line.strip()
            if line.startswith("#BEAT INFO"):
                in_beat_info = True
            elif line.startswith("#END") and in_beat_info:
                in_beat_info = False
            elif in_beat_info:
                parts = line.split('\t')
                if len(parts) >= 3:
                    measure_info, beats, ticks = parts[0], parts[1], parts[2]
                    measure, beat, tick = map(int, measure_info.split(','))
                    beat_info.append({
                        'measure': measure,
                        'beat': beat,
                        'tick': tick,
                        'beats_per_measure': int(beats),
                        'ticks_per_beat': int(ticks)  
                    })
    return beat_info

def get_end_position(filepath):
    """
    Retrieves the end position of the chart from a VOX file.

    :param filepath: Path to the VOX file.
    :return: Tuple representing the end position (measure, beat, tick).
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#END POSITION"):
                if i + 1 >= len(lines):
                    print("Unexpected end of file after #END POSITION")
                    return None

                next_line = lines[i + 1].strip()  

                if next_line.startswith("#END"):
                    continue  

                measure_info = next_line.split(',')[0:3]
                measure, beat, tick = map(int, measure_info)
                return (measure, beat, tick)

    return None  


def generate_timestamps(beat_info, end_position):
    """
    Generates all timestamps from the start of the chart to the end position.

    :param beat_info: List of time sig change points.
    :param end_position: Tuple representing the end position (measure, beat, tick).
    :return: List of timestamps (each a string in the format 'measure,beat,tick').
    """
    timestamps = []
    ticks_per_beat = 48 
    current_beat_info_index = 0

    for measure in range(1, end_position[0] + 1):
        while current_beat_info_index < len(beat_info) - 1 and measure >= beat_info[current_beat_info_index + 1]['measure']:
            current_beat_info_index += 1

        beats_per_measure = beat_info[current_beat_info_index]['beats_per_measure']

        for beat in range(1, beats_per_measure + 1):
            for tick in range(0, ticks_per_beat):
                if (measure, beat, tick) > end_position:
                    return timestamps 
                timestamp = f"{measure:03},{beat:02},{tick:02}"
                timestamps.append(timestamp)

    return timestamps

def create_directory_for_files(original_file_path):
    directory_name = os.path.splitext(os.path.basename(original_file_path))[0]

    new_directory_path = os.path.join(os.path.dirname(original_file_path), directory_name)

    if not os.path.exists(new_directory_path):
        os.makedirs(new_directory_path)

    return new_directory_path

def generate_all_combinations(elements):
    return list(itertools.permutations(elements))

def randomize_tracks(track_data):
    tracks_to_randomize = ['TRACK3', 'TRACK4', 'TRACK5', 'TRACK6']
    
    original_tracks = {track: track_data[track] for track in tracks_to_randomize + ['TRACK2', 'TRACK7']} 

    random.shuffle(tracks_to_randomize)

    for i, shuffled_track in enumerate(tracks_to_randomize):
        original_track = 'TRACK' + str(i+3)  
        track_data[shuffled_track] = original_tracks[original_track]

    swap_tracks_2_and_7 = random.choice([True, False])  
    if swap_tracks_2_and_7:
        track_data['TRACK2'], track_data['TRACK7'] = track_data['TRACK7'], track_data['TRACK2']

    randomized_order = tracks_to_randomize.copy()  
    if swap_tracks_2_and_7:
        randomized_order.extend(['TRACK7', 'TRACK2']) 
    else:
        randomized_order.extend(['TRACK2', 'TRACK7']) 

    return track_data, randomized_order 

def parse_file(filepath):
    if not os.path.exists(filepath):
        print("File not found!")
        return None

    tracks = {f"TRACK{num}": [] for num in range(1, 9)}

    current_track = None
    with open(filepath, 'r') as file:
        for line_number, line in enumerate(file, 1): 
            line = line.strip()
            #print(f"Reading line {line_number}: {line}") 
            if line.startswith("#TRACK") and line[6] in "12345678":
                current_track = line[1:]
            elif line.startswith("#END"):
                current_track = None
            elif current_track:
                tracks[current_track].append(line)

    return tracks

def write_to_file(filepath, track_data, full_content):
    new_file_path = filepath.replace('.vox', '.vox')

    with open(new_file_path, 'w') as file:
        in_track_section = False
        current_track = None

        for line in full_content:
            if line.startswith("#TRACK") and line[6] in "12345678":
                in_track_section = True
                current_track = line[1:]
                file.write(line + '\n')  

                for track_line in track_data[current_track]:
                    file.write(track_line + '\n')

            elif line.startswith("#END") and in_track_section:
                in_track_section = False
                current_track = None
                file.write(line + '\n')  

            elif not in_track_section:
                file.write(line + '\n') 

def main():
    parser = argparse.ArgumentParser(description='Randomize VOX files.')
    parser.add_argument('file_path', type=str, help='Path to VOX to random.')
    parser.add_argument('-s', '--s-random', action='store_true', help='apply s-ram.')

    args = parser.parse_args()

    file_path = args.file_path  

    if not os.path.exists(file_path):
        print("File not found!")
        return

    s_random = args.s_random 

    with open(file_path, 'r') as file:
        full_content = [line.strip() for line in file]

    beat_info = parse_beat_info(file_path)
    end_position = get_end_position(file_path)

    if not end_position:
        print("Could not find the end position in the file.")
        return

    timestamps = generate_timestamps(beat_info, end_position)

    track_data = parse_file(file_path)

    structured_notes = parse_notes_in_tracks(track_data)

    sorted_chip_timestamps = identify_chip_timestamps(structured_notes)
    print(sorted_chip_timestamps)

    #TODO add hold end timestamps too, to calculate the occupied times
    sorted_hold_timestamps = identify_hold_timestamps(structured_notes)
    print(sorted_hold_timestamps)

    if track_data:
        original_order = ['a', 'b', 'c', 'd', 'L', 'R'] 

        all_button_combinations = generate_all_combinations(['a', 'b', 'c', 'd'])
        all_fx_combinations = generate_all_combinations(['L', 'R'])

        new_directory = create_directory_for_files(file_path)

        track_identifiers_inverse = {'a': 'TRACK3', 'b': 'TRACK4', 'c': 'TRACK5', 'd': 'TRACK6', 'L': 'TRACK2', 'R': 'TRACK7'}

        original_keys = ['TRACK1', 'TRACK8']  

        base_file_name = os.path.splitext(os.path.basename(file_path))[0]

        # Iterate over all combinations
        for button_combination in all_button_combinations:
            for fx_combination in all_fx_combinations:
                specific_order = list(button_combination) + list(fx_combination)

                specific_track_order = [track_identifiers_inverse[item] for item in specific_order]

                new_track_data = {}
                for original_key, new_key in zip(original_keys + specific_track_order, original_keys + ['TRACK3', 'TRACK4', 'TRACK5', 'TRACK6', 'TRACK2', 'TRACK7']):
                    new_track_data[new_key] = track_data[original_key]

                new_file_name = f"{base_file_name}_ran_{''.join(specific_order)}.vox"
                new_file_path = os.path.join(new_directory, new_file_name)

                write_to_file(new_file_path, new_track_data, full_content)

if __name__ == "__main__":
    main()
