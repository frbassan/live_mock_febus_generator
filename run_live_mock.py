import h5py
import numpy as np
import time
import os

# Create file in the same folder as this script
folder_name = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(folder_name, "mock_febus_data_10k_rotating.h5")

num_points = 10000
max_traces = 10   # Rewrites file after reaching this amount of traces

distances = np.linspace(0, 10000, num_points)
base_temp = 25.0
base_strain = 0.0

# Some static hotspots slightly randomized in time
hotspots = [
    {"start": 3200, "end": 3300, "intensity": 45.0},   # Critical leak
    {"start": 4200, "end": 4250, "intensity": 25.0},   # Fire in nearby vegetation
    {"start": 9100, "end": 9105, "intensity": 60.0}    # Extremely high point short-circuit
]

strain_spots = [
    {"start": 4800, "end": 4850, "intensity": 800.0},   # Suddenly opening crack
    {"start": 6200, "end": 6300, "intensity": 400.0},   # Landslide tensioning cable
]

print(f"Starting live rotating generator... Data will be written to:")
print(f"{filename}")
print(f"Generating 1 trace per second. Rewriting file every {max_traces} traces.\n")

try:
    cycle = 1
    while True:
        print(f"\n--- Starting Cycle {cycle} --- (File recreated space for 0 to {max_traces} traces)")
        
        # Open in 'w' mode to overwrite completely
        with h5py.File(filename, 'w') as f:
            f.create_dataset("distances", data=distances)
            
            # Max shape allows resizing along the first axis row by row without crashing
            dset_temp = f.create_dataset("extractedTemperature", 
                                         shape=(0, num_points), 
                                         maxshape=(max_traces, num_points), 
                                         chunks=(1, num_points), 
                                         compression="gzip")
            dset_strain = f.create_dataset("extractedDeformation", 
                                           shape=(0, num_points), 
                                           maxshape=(max_traces, num_points), 
                                           chunks=(1, num_points), 
                                           compression="gzip")
            
            f.attrs['interrogator_model'] = "FEBUS G2-R (Live Rotating)"
            f.attrs['location'] = "TS Conductor Mega Test Site"
            f.attrs['pulse_width_ns'] = 10.0
            
            for i in range(max_traces):
                start_time = time.time()
                
                # Generate 1 trace of noise
                temp_trace = base_temp + np.random.normal(0, 5, (1, num_points))
                strain_trace = base_strain + np.random.normal(0, 100, (1, num_points))
                
                # Apply spots (adding random variations to simulate "live" behavior)
                for hs in hotspots:
                    variation = np.random.normal(0, 2)
                    temp_trace[0, hs["start"]:hs["end"]] += (hs["intensity"] + variation)
                    
                for ss in strain_spots:
                    variation = np.random.normal(0, 20)
                    strain_trace[0, ss["start"]:ss["end"]] += (ss["intensity"] + variation)
                
                # Resize and append the trace
                dset_temp.resize(i + 1, axis=0)
                dset_temp[i, :] = temp_trace[0, :]
                
                dset_strain.resize(i + 1, axis=0)
                dset_strain[i, :] = strain_trace[0, :]
                
                # Flush to ensure other programs (like h5_viewer) can see new traces as they are written
                f.flush() 
                
                print(f"Generated trace {i+1}/{max_traces}", end='\r')
                
                # Wait for the remainder of the 1-second interval
                elapsed = time.time() - start_time
                sleep_time = max(0, 1.0 - elapsed)
                time.sleep(sleep_time)
                
        print("\nRewriting limit reached. Overwriting file...")
        cycle += 1

except KeyboardInterrupt:
    print("\nGenerator stopped by user.")
