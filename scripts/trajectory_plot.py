from copy import copy
from pathlib import Path
from sys import path
 
# Path to the build directory including a file similar to 'ruckig.cpython-37m-x86_64-linux-gnu'.
build_path = Path(__file__).parent.absolute().parent / 'build'
path.insert(0, str(build_path))
 
from ruckig import InputParameter, OutputParameter, Result, Ruckig
import matplotlib.pyplot as plt 

if __name__ == '__main__':
    # Create instances: the Ruckig OTG as well as input and output parameters
    otg = Ruckig(1, 0.01)  # DoFs, control cycle
    inp = InputParameter(1)
    out = OutputParameter(1)
 
    # Set input parameters
    inp.current_position = [0.0]
    inp.current_velocity = [0.0]
    inp.current_acceleration = [0.0]
 
    inp.target_position = [5.0]
    inp.target_velocity = [0.0]
    inp.target_acceleration = [0.0]
 
    inp.max_velocity = [3.0]
    inp.max_acceleration = [3.0]
    inp.max_jerk = [1000000000]
    # Generate the trajectory within the control loop
    first_output, out_list = None, []
    positions, speeds, accelerations, times = [], [], [], []
    res = Result.Working
    while res == Result.Working:
        res = otg.update(inp, out)
 
        out_list.append(copy(out))
        times.append(out.time)
        positions.append(out.new_position)
        speeds.append(out.new_velocity)
        accelerations.append(out.new_acceleration)
        out.pass_to_input(inp)
 
        if not first_output:
            first_output = copy(out)

    plt.plot(times, speeds)
    plt.plot(times, positions)
    plt.plot(times, accelerations)