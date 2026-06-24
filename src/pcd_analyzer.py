import numpy as np

def analyze_acoustic_feedback(raw_signal, sampling_rate, driving_freq, tof_gate_start, tof_gate_end):
    """
    Processes raw acoustic feedback to differentiate between skull reflections and particle disintegration.
    
    Parameters:
    - raw_signal: 1D numpy array of voltage/pressure values from the listening actuator.
    - sampling_rate: Sampling rate of the digitizer in Hz (e.g., 10e6 for 10 MHz).
    - driving_freq: The acoustic transmission frequency in Hz (e.g., 1e6 for 1 MHz).
    - tof_gate_start: Microseconds to wait before opening the listening gate (ignores skull).
    - tof_gate_end: Microseconds to stop recording the target window.
    
    Returns:
    - is_shattered (bool): True if broadband noise crosses threshold, False otherwise.
    - metrics (dict): Calculated noise thresholds and metrics for the ML feedback loop.
    """
    # -------------------------------------------------------------
    # STAGE 1: Temporal Gating (Time-of-Flight Isolation)
    # -------------------------------------------------------------
    time_vector = np.arange(len(raw_signal)) / sampling_rate
    
    # Convert microsecond inputs to seconds
    start_sec = tof_gate_start * 1e-6
    end_sec = tof_gate_end * 1e-6
    
    # Isolate data strictly within our target "deep brain" window
    gate_mask = (time_vector >= start_sec) & (time_vector <= end_sec)
    gated_signal = raw_signal[gate_mask]
    
    if len(gated_signal) == 0:
        return False, {"error": "Target window empty. Check Time-of-Flight parameters."}

    # -------------------------------------------------------------
    # STAGE 2: Spectral Transformation (FFT)
    # -------------------------------------------------------------
    n_samples = len(gated_signal)
    fft_values = np.fft.rfft(gated_signal)
    fft_freqs = np.fft.rfftfreq(n_samples, d=1.0/sampling_rate)
    
    # Calculate magnitude spectrum in decibels
    magnitude = np.abs(fft_values)
    magnitude_db = 20 * np.log10(magnitude + 1e-9) # 1e-9 avoids log(0)

    # -------------------------------------------------------------
    # STAGE 3: Spectral Disambiguation (Broadband Filter)
    # -------------------------------------------------------------
    # We define the fundamental and harmonic frequencies to exclude them from the noise floor
    harmonics = [driving_freq * i for i in range(1, 5)] # 1MHz, 2MHz, 3MHz, 4MHz
    exclusion_bandwidth = 50e3 # Exclude +/- 50 kHz around each harmonic peak
    
    broadband_mask = np.ones(len(fft_freqs), dtype=bool)
    for h in harmonics:
        # Mask out the predictable linear reflections from the skull/tissue
        broadband_mask &= ~((fft_freqs >= h - exclusion_bandwidth) & (fft_freqs <= h + exclusion_bandwidth))
    
    # Isolate the chaotic non-linear noise generated strictly by fracturing
    broadband_energy = np.mean(magnitude_db[broadband_mask])
    
    # -------------------------------------------------------------
    # STAGE 4: Decision Matrix
    # -------------------------------------------------------------
    # Baseline threshold determined by lab calibration on standard hydrogel
    DISINTEGRATION_THRESHOLD_DB = -45.0 
    
    is_shattered = broadband_energy > DISINTEGRATION_THRESHOLD_DB
    
    metrics = {
        "broadband_energy_db": float(broadband_energy),
        "threshold_limit_db": DISINTEGRATION_THRESHOLD_DB,
        "samples_analyzed": n_samples
    }
    
    return is_shattered, metrics

# =====================================================================
# SYSTEM VERIFICATION TEST (Simulating a real-world scenario)
# =====================================================================
if __name__ == "__main__":
    # Setup test simulation parameters
    FS = int(20e6)          # 20 MHz Digitizer Sampling Rate
    DURATION = 100e-6       # 100 microseconds total capture time
    F0 = int(1e6)           # 1 MHz Driving Pulse
    t = np.arange(int(FS * DURATION)) / FS
    
    print("[1/3] Generating simulated post-fire acoustic environment...")
    # Simulate a massive, early reflection bouncing off the skull (0 to 8 microseconds)
    skull_reflection = np.sin(2 * np.pi * F0 * t) * np.exp(-((t - 4e-6) / 2e-6)**2) * 5.0
    
    # Simulate a true particle fracture event occurring deep in the matrix (~20 microseconds)
    # This generates a chaotic white-noise burst (broadband emission) rather than a clean tone
    np.random.seed(42) # For reproducible test results
    fracture_noise = np.random.normal(0, 0.3, len(t)) * np.exp(-((t - 20e-6) / 3e-6)**2)
    
    # Combine signals along with general systemic ambient noise
    simulated_raw_audio = skull_reflection + fracture_noise + np.random.normal(0, 0.01, len(t))
    
    print("[2/3] Passing raw signal to the ATAN-NT Processing Engine...")
    # Run the analyzer: Gate out the skull reflection (0-10us) and listen only to 12-35us
    success, data = analyze_acoustic_feedback(
        raw_signal=simulated_raw_audio, 
        sampling_rate=FS, 
        driving_freq=F0, 
        tof_gate_start=12, 
        tof_gate_end=35
    )
    
    print("\n================ SYSTEM DIAGNOSTIC REPORT ================")
    print(f"Target Disintegration Event Verified: {success.upper() if isinstance(success, str) else success}")
    print(f"Measured Inter-Harmonic Energy Level: {data['broadband_energy_db']:.2f} dB")
    print(f"System Operational Safety Threshold : {data['threshold_limit_db']:.2f} dB")
    print("==========================================================")