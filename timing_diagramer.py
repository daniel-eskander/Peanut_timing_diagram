import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def calculate_ideal_logical_pbits(number_of_hw_pbits, synaptic_sum_time, hw_process_time_ns, clk_frequency):
    cycle_time_ns = 1e9 / clk_frequency
    synaptic_sum_time_ns = synaptic_sum_time * cycle_time_ns
    ideal_logical_pbits = max(1, round(number_of_hw_pbits * synaptic_sum_time_ns / hw_process_time_ns))
    return ideal_logical_pbits

def generate_gantt_diagram(synaptic_sum_time, hw_process_time_ns, number_of_hw_pbits, number_of_logical_pbits, clk_frequency, number_of_iterations):
    cycle_time_ns = 1e9 / clk_frequency
    synaptic_sum_ns = synaptic_sum_time * cycle_time_ns
    one_clock_cycle_ns = cycle_time_ns

    fig, ax = plt.subplots(figsize=(12, 8))

    hw_process_y_pos_base = -1
    synaptic_sum_y_pos_base = 0

    hw_end_times = [0] * number_of_hw_pbits
    sp_end_times = [0] * number_of_logical_pbits
    sp_start_times = [0] * number_of_logical_pbits

    last_global_sp_start_time = 0
    max_time_ns = 0
    hw_first_time_started = [False] * number_of_hw_pbits

    total_idle_time = 0  # Track total system idle time
    total_hw_idle_time = 0  # Track total hardware idle time
    total_fpga_idle_time = 0  # Track total FPGA (synaptic calculator) idle time
    total_updates = number_of_iterations  # Track the total number of updates

    for i in range(number_of_iterations):
        next_sp_start_time_global = last_global_sp_start_time + one_clock_cycle_ns
        sp_pbit = sp_end_times.index(min(sp_end_times))
        earliest_hw_ready_time = min(hw_end_times)
        hw_pbit = hw_end_times.index(earliest_hw_ready_time)
        start_time_synaptic_sum = max(next_sp_start_time_global, sp_end_times[sp_pbit])
        sp_delay_time = max(0, earliest_hw_ready_time - synaptic_sum_ns)
        start_time_synaptic_sum = max(start_time_synaptic_sum, sp_delay_time)

        idle_time_ns_synaptic = start_time_synaptic_sum - (last_global_sp_start_time + one_clock_cycle_ns)
        idle_time_ns_synaptic = min(idle_time_ns_synaptic, start_time_synaptic_sum - sp_end_times[sp_pbit])

        if idle_time_ns_synaptic > 0:
            idle_rect = mpatches.Rectangle(
                (start_time_synaptic_sum - idle_time_ns_synaptic, synaptic_sum_y_pos_base + sp_pbit * 2), 
                idle_time_ns_synaptic, 1, color='gray', alpha=0.5)
            ax.add_patch(idle_rect)
            total_idle_time += idle_time_ns_synaptic  # Accumulate total system idle time
            total_fpga_idle_time += idle_time_ns_synaptic  # Accumulate FPGA idle time (synaptic calculator)

        rect = mpatches.Rectangle(
            (start_time_synaptic_sum, synaptic_sum_y_pos_base + sp_pbit * 2), 
            synaptic_sum_ns, 1, color='blue', alpha=0.6)
        ax.add_patch(rect)
        ax.text(
            start_time_synaptic_sum + synaptic_sum_ns / 2, 
            synaptic_sum_y_pos_base + sp_pbit * 2 + 0.5, 
            f'SP{sp_pbit+1}', ha='center', va='center', fontsize=6, color='black')

        sp_start_times[sp_pbit] = start_time_synaptic_sum
        sp_end_times[sp_pbit] = start_time_synaptic_sum + synaptic_sum_ns
        last_global_sp_start_time = start_time_synaptic_sum

        start_time_hw_process = max(hw_end_times[hw_pbit], start_time_synaptic_sum + synaptic_sum_ns)
        previous_hw_end_time = hw_end_times[hw_pbit]
        hw_idle_time_ns = max(0, start_time_hw_process - previous_hw_end_time)
        
        if hw_first_time_started[hw_pbit]:
            if hw_idle_time_ns > 0:
                hw_idle_rect = mpatches.Rectangle(
                    (previous_hw_end_time, hw_process_y_pos_base - hw_pbit * 2), 
                    hw_idle_time_ns, 1, color='gray', alpha=0.5)
                ax.add_patch(hw_idle_rect)
                total_idle_time += hw_idle_time_ns  # Accumulate total system idle time
                total_hw_idle_time += hw_idle_time_ns  # Accumulate hardware idle time

        hw_first_time_started[hw_pbit] = True

        rect = mpatches.Rectangle(
            (start_time_hw_process, hw_process_y_pos_base - hw_pbit * 2), 
            hw_process_time_ns, 1, color='green', alpha=0.6)
        ax.add_patch(rect)
        ax.text(
            start_time_hw_process + hw_process_time_ns / 2, 
            hw_process_y_pos_base - hw_pbit * 2 + 0.5, 
            f'HWP{hw_pbit+1}', ha='center', va='center', fontsize=6, color='black')

        ax.annotate('', xy=(start_time_hw_process, hw_process_y_pos_base - hw_pbit * 2 + 0.5), 
                    xytext=(start_time_synaptic_sum + synaptic_sum_ns, synaptic_sum_y_pos_base + sp_pbit * 2 + 0.5),
                    arrowprops=dict(arrowstyle="->", linestyle='dotted', color='black'))

        hw_end_times[hw_pbit] = start_time_hw_process + hw_process_time_ns
        max_time_ns = max(max_time_ns, start_time_hw_process + hw_process_time_ns)

    total_time_ns = max_time_ns  # Total simulation time in nanoseconds
    avg_update_time_ns = total_time_ns / total_updates  # Average update time in nanoseconds

    # Print total idle time breakdown
    print(f"Total Time (ns): {total_time_ns}")
    print(f"Total Hardware Idle Time (ns): {total_hw_idle_time}")
    print(f"Total FPGA Idle Time (ns): {total_fpga_idle_time}")
    print(f"Total System Idle Time (ns): {total_idle_time}")
    print(f"Average update cycle time for one logical Pbit (ns): {avg_update_time_ns}")

    ax.set_xlim(0, max_time_ns + 50)
    ax.set_ylim(hw_process_y_pos_base - number_of_hw_pbits * 2 - 2, synaptic_sum_y_pos_base + number_of_logical_pbits * 2 + 1)

    ax.set_xlabel('Time (ns)')
    
    # Add y-axis labels for logical Pbits and HW Pbits
    for i in range(number_of_logical_pbits):
        ax.text(-100, synaptic_sum_y_pos_base + i * 2 + 0.5, f'Logical_Pbit {i+1}', va='center', ha='right', fontsize=10, color='blue')

    for i in range(number_of_hw_pbits):
        ax.text(-100, hw_process_y_pos_base - i * 2 + 0.5, f'HW_Pbit {i+1}', va='center', ha='right', fontsize=10, color='green')

    ax.text(-50, synaptic_sum_y_pos_base + (number_of_logical_pbits * 2) / 2, 'Synaptic Calculator', 
        va='center', ha='center', rotation='vertical', fontsize=10)
    ax.text(-50, hw_process_y_pos_base - (number_of_hw_pbits * 2) / 2, 'Hardware', 
        va='center', ha='center', rotation='vertical', fontsize=10)

    # Option to add transparent vertical lines for clock cycles
    # for tick in range(0, int(max_time_ns), int(one_clock_cycle_ns)):
    #     ax.axvline(x=tick, color='lightgray', linestyle='--', alpha=0.3)

    ax.set_yticks([])

    # Adding a legend
    legend_handles = [
        mpatches.Patch(color='blue', label='FPGA'),
        mpatches.Patch(color='green', label='Hardware'),
        mpatches.Patch(color='gray', label='Idle Time')
    ]
    ax.legend(handles=legend_handles, loc='upper right')

    plt.title('Timing Diagram')
    plt.show()
