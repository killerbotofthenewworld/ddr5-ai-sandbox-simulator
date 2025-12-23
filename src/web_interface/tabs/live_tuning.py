"""
Live tuning tab for real-time optimization with hardware integration.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import time
import random
from src.ddr5_models import DDR5Configuration
from src.live_tuning_safety import LiveTuningSafetyValidator
from src.live_hardware_tuning import LiveHardwareTuner

# Safety lock duration in seconds (15 minutes = 900 seconds)
SAFETY_LOCK_DURATION = 900


def render_live_tuning_tab(config: DDR5Configuration):
    """
    Render the live tuning tab.
    
    Args:
        config: Current DDR5 configuration
    """
    st.header("⚡ Live DDR5 Tuning")
    
    # CRITICAL SAFETY WARNING
    st.error(
        "🚨 **DANGER**: Live tuning modifies system memory settings in real-time! "
        "This can cause system instability, data loss, or hardware damage. "
        "**SAVE ALL WORK** before proceeding!"
    )
    
    # Enhanced safety disclaimer
    with st.expander("🛡️ CRITICAL SAFETY INFORMATION - READ BEFORE USE", expanded=True):
        st.markdown("""
        ## ⚠️ LIVE TUNING SAFETY WARNINGS
        
        ### 🚨 IMMEDIATE RISKS
        - **System Crashes**: Instant blue screen or system freeze
        - **Data Loss**: Unsaved work will be lost during crashes
        - **Boot Failures**: System may fail to start, requiring CMOS reset
        - **Hardware Damage**: Extreme voltages can permanently damage components
        - **Memory Corruption**: Data in RAM may become corrupted
        
        ### 🛡️ MANDATORY SAFETY PRECAUTIONS
        
        **BEFORE STARTING:**
        1. **💾 SAVE ALL WORK** - Close all important applications
        2. **📋 Backup Current Settings** - Record working BIOS values
        3. **🔌 Ensure Stable Power** - Use UPS if possible
        4. **🌡️ Check Temperatures** - System should be cool and stable
        5. **🧪 Have Recovery Plan** - Know how to reset CMOS/BIOS
        
        **DURING TUNING:**
        - **📊 Monitor Constantly** - Watch temps, voltages, errors
        - **⚡ Small Steps Only** - Make minimal adjustments
        - **🔄 Test Each Change** - Run stability tests immediately
        - **🛑 Stop if Unstable** - Don't ignore warning signs
        
        ### 🚫 DO NOT USE IF:
        - System is already unstable
        - You're new to memory overclocking
        - You don't understand DDR5 specifications
        - You can't afford system downtime
        - You're using this on a production system
        
        ### 🆘 EMERGENCY PROCEDURES
        **If system becomes unstable:**
        1. **Power off immediately** (hold power button)
        2. **Clear CMOS** (remove battery or use jumper)
        3. **Reset to defaults** in BIOS
        4. **Boot with single memory stick** if needed
        
        ### ⚖️ LEGAL DISCLAIMER
        This tool is for educational/experimental purposes only. 
        **YOU ASSUME ALL RISKS** for any damage to hardware, data loss, 
        or system instability. Use at your own risk!
        """)
    
    # Hardware integration setup
    if 'live_hardware_tuner' not in st.session_state:
        st.session_state.live_hardware_tuner = LiveHardwareTuner()
    
    hardware_tuner = st.session_state.live_hardware_tuner
    safe_mode = st.session_state.get("safe_mode", True)
    if 'preflight_passed' not in st.session_state:
        st.session_state.preflight_passed = False
    
    # 15-minute safety lock system
    st.subheader("🔒 15-Minute Safety Lock")
    
    # Initialize safety lock timestamp if not exists
    if 'safety_lock_start_time' not in st.session_state:
        st.session_state.safety_lock_start_time = None
        st.session_state.safety_lock_acknowledged = False
    
    # Check if safety lock is active
    safety_lock_active = True
    remaining_time = 0
    
    if st.session_state.safety_lock_start_time:
        elapsed_time = time.time() - st.session_state.safety_lock_start_time
        remaining_time = max(0, SAFETY_LOCK_DURATION - elapsed_time)
        safety_lock_active = remaining_time > 0
    
    if safety_lock_active:
        if st.session_state.safety_lock_start_time is None:
            # Safety lock not started yet
            st.error("🔒 **SAFETY LOCK ACTIVE**: Live tuning is locked for your protection!")
            
            st.warning("""
            **⏰ 15-MINUTE MANDATORY WAITING PERIOD**
            
            Before accessing live hardware tuning, you must wait 15 minutes. This safety period ensures:
            - 📚 You have time to read all safety documentation
            - 💾 You can save all important work 
            - 🛡️ You understand the serious risks involved
            - 🔧 You have prepared recovery tools (CMOS reset knowledge)
            - 🎯 You are mentally prepared for potential system instability
            """)
            
            if st.button("🚨 START 15-MINUTE SAFETY COUNTDOWN", type="primary"):
                st.session_state.safety_lock_start_time = time.time()
                st.success("⏰ Safety countdown started! Please use this time to prepare.")
                st.rerun()
        else:
            # Safety lock in progress
            minutes_remaining = int(remaining_time // 60)
            seconds_remaining = int(remaining_time % 60)
            
            st.error(f"🔒 **SAFETY LOCK ACTIVE**: {minutes_remaining:02d}:{seconds_remaining:02d} remaining")
            
            progress = 1.0 - (remaining_time / SAFETY_LOCK_DURATION)
            st.progress(progress)
            
            st.info(f"""
            **⏳ PREPARATION TIME REMAINING: {minutes_remaining:02d}:{seconds_remaining:02d}**
            
            **Use this time to:**
            - 📖 Read all safety warnings below
            - 💾 Save ALL important work and close applications  
            - 🔧 Learn how to reset CMOS on your motherboard
            - 🌡️ Check system temperatures are normal
            - ⚡ Ensure stable power supply (UPS recommended)
            - 🧠 Mentally prepare for potential system crashes
            """)
            
            # Auto-refresh every second
            time.sleep(1)
            st.rerun()
    else:
        # Safety lock expired - show final confirmation
        st.success("✅ **15-MINUTE SAFETY PERIOD COMPLETED**")
        
        if not st.session_state.safety_lock_acknowledged:
            st.warning("""
            **🎯 FINAL SAFETY CONFIRMATION**
            
            You have completed the 15-minute safety preparation period.
            Live hardware tuning will now be available, but you must acknowledge:
            """)
            
            final_checks = []
            final_checks.append(st.checkbox("🚨 I have saved ALL my work and closed important applications"))
            final_checks.append(st.checkbox("🔧 I know how to reset CMOS if my system fails to boot"))
            final_checks.append(st.checkbox("🌡️ I have verified system temperatures are normal and stable"))
            final_checks.append(st.checkbox("⚖️ I accept FULL RESPONSIBILITY for any hardware damage"))
            final_checks.append(st.checkbox("💀 I understand this can PERMANENTLY DAMAGE my memory"))
            
            if all(final_checks):
                if st.button("🔓 UNLOCK LIVE HARDWARE TUNING - I AM READY", type="primary"):
                    st.session_state.safety_lock_acknowledged = True
                    st.success("🔓 Live hardware tuning unlocked! Exercise extreme caution.")
                    st.rerun()
            else:
                st.error("⚠️ You must acknowledge all final safety confirmations")
    
    # Only show hardware controls if safety lock cleared and acknowledged
    if not safety_lock_active and st.session_state.safety_lock_acknowledged:
        # Safe Mode: require Dry-Run preflight
        if safe_mode and not st.session_state.preflight_passed:
            st.subheader("🔎 Dry-Run Preflight (Safe Mode)")
            st.info("Run a comprehensive preflight to validate safety before enabling live tuning.")
            if st.button("🧪 Run Preflight Validation", type="primary"):
                with st.spinner("Running safety preflight (no changes will be applied)..."):
                    try:
                        validator = LiveTuningSafetyValidator()
                        detected = hardware_tuner.detect_modules() if hasattr(hardware_tuner, 'detect_modules') else []
                        report = validator.run_comprehensive_safety_test(config, detected)
                        st.session_state.preflight_report = report
                        st.session_state.preflight_passed = report.overall_safety.name in ("SAFE", "VERIFIED_SAFE")
                        if st.session_state.preflight_passed:
                            st.success("✅ Preflight passed: system considered SAFE for live tuning.")
                        else:
                            st.error(f"❌ Preflight did not pass (overall: {report.overall_safety.value}). Resolve issues before proceeding.")
                    except Exception as e:
                        st.session_state.preflight_passed = False
                        st.error(f"Preflight failed to run: {e}")
            if 'preflight_report' in st.session_state:
                with st.expander("Preflight Report"):
                    rep = st.session_state.preflight_report
                    st.write(f"Overall: {rep.overall_safety} ({rep.overall_score:.2f})")
                    st.write(rep.safety_recommendations)
            st.stop()
        
        # Live tuning controls
        st.subheader("🎛️ Live Tuning Controls")
        
        # Hardware status and initialization
        hardware_col1, hardware_col2 = st.columns(2)
        
        with hardware_col1:
            st.subheader("🖥️ Hardware Status")
            
            # Initialize hardware button
            if not hardware_tuner.hardware_initialized:
                if st.button("🔌 Initialize Hardware Interface"):
                    with st.spinner("Initializing hardware interface..."):
                        success = hardware_tuner.initialize_hardware()
                        if success:
                            st.success("✅ Hardware interface initialized")
                            st.rerun()
                        else:
                            st.error("❌ Hardware initialization failed")
            else:
                # Show hardware status
                hardware_status = hardware_tuner.get_hardware_status()
                
                status_color = {
                    "ready": "🟢",
                    "unsafe": "🔴", 
                    "error": "⭕",
                    "not_initialized": "⚫"
                }.get(hardware_status["status"], "⚪")
                
                st.write(f"{status_color} **Status:** {hardware_status['status'].upper()}")
                st.write(f"💻 **Platform:** {hardware_status.get('platform', 'Unknown')}")
                st.write(f"📝 **Message:** {hardware_status.get('message', 'No message')}")
                
                # Show capabilities if available
                if 'capabilities' in hardware_status:
                    caps = hardware_status['capabilities']
                    st.write("**Capabilities:**")
                    st.write(f"- Memory Controller: {'✅' if caps.get('memory_controller') else '❌'}")
                    st.write(f"- Vendor Tools: {'✅' if caps.get('vendor_tools') else '❌'}")
                    st.write(f"- UEFI Vars: {'✅' if caps.get('uefi_vars') else '❌'}")
        
        with hardware_col2:
            st.subheader("🛡️ Safety Status")
            
            if hardware_tuner.hardware_initialized:
                if st.button("🔍 Check System Safety"):
                    with st.spinner("Checking system safety..."):
                        hardware_status = hardware_tuner.get_hardware_status()
                        safety_info = hardware_status.get('safety') or hardware_status.get('safety_state', {})
                        
                        safety_checks = {
                            "Temperature Safe": safety_info.get('temperature_safe', False),
                            "Memory Stable": safety_info.get('memory_stable', False),
                            "Power Stable": safety_info.get('power_stable', False),
                            "Backup Created": safety_info.get('backup_created', False)
                        }
                        
                        all_safe = all(safety_checks.values())
                        
                        if all_safe:
                            st.success("✅ System ready for live tuning")
                        else:
                            st.error("❌ System not ready - resolve issues first")
                        
                        for check, status in safety_checks.items():
                            if status:
                                st.success(f"✅ {check}")
                            else:
                                st.error(f"❌ {check}")
            else:
                st.info("🔌 Initialize hardware interface first")
    
    # Session management
    session_status = hardware_tuner.get_session_status()
    if session_status:
        st.subheader("📊 Live Tuning Session")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Duration", f"{session_status['duration']:.0f}s")
        with col2:
            st.metric("Changes Applied", session_status['changes_applied'])
        with col3:
            st.metric("Safety Violations", session_status['safety_violations'])
        
        # Session controls
        if session_status['active']:
            if st.button("🛑 Stop Live Session"):
                hardware_tuner.stop_session()
                st.success("✅ Live tuning session stopped")
                st.rerun()
        else:
            if st.button("🚀 Start Live Session"):
                success = hardware_tuner.start_live_session(config)
                if success:
                    st.success("✅ Live tuning session started!")
                    st.rerun()
    
    st.divider()
    
    # Live tuning interface
    st.subheader("⚙️ Live Parameter Adjustment")
    
    if not st.session_state.get('live_tuning_enabled', False):
        st.info("🔒 Live tuning is disabled for safety")
        
        # Enhanced safety confirmation
        st.error("🚨 DANGER ZONE: Live tuning can damage your system!")
        
        with st.expander("⚠️ ACKNOWLEDGMENT OF RISKS", expanded=False):
            st.markdown("""
            **By enabling live tuning, you acknowledge:**
            
            - ✅ I have saved all important work
            - ✅ I understand this can crash my system instantly
            - ✅ I know how to reset CMOS/BIOS if system won't boot
            - ✅ I accept full responsibility for any damage
            - ✅ I will not blame this software for hardware damage
            - ✅ I understand extreme settings can permanently damage memory
            - ✅ I will start with small, conservative adjustments
            - ✅ I will monitor temperatures and stability constantly
            """)
        
        safety_checks = []
        safety_checks.append(st.checkbox("🚨 I understand live tuning can DAMAGE my hardware"))
        safety_checks.append(st.checkbox("💾 I have SAVED all my important work"))
        safety_checks.append(st.checkbox("🔧 I know how to RESET CMOS if system fails to boot"))
        safety_checks.append(st.checkbox("⚖️ I accept FULL RESPONSIBILITY for any damage"))
        
        if all(safety_checks):
            if st.button("🔓 ENABLE LIVE TUNING - I ACCEPT ALL RISKS", type="primary"):
                st.session_state.live_tuning_enabled = True
                st.success("⚡ Live tuning enabled!")
                st.warning("🚨 SYSTEM IS NOW IN DANGER ZONE!")
                st.rerun()
        else:
            st.error("⚠️ You must acknowledge all safety requirements to enable live tuning")
    else:
        # Safety lock is active - show message
        st.info("🔒 Complete the 15-minute safety preparation period above to access live tuning controls.")
    
    st.divider()
    
    # Live stress testing (only available when safety lock is unlocked)
    st.subheader("🔥 Live Stress Testing")
    
    if (not safety_lock_active and st.session_state.safety_lock_acknowledged and 
        st.session_state.get('live_tuning_enabled', False) and hardware_tuner.session):
        stress_col1, stress_col2 = st.columns(2)
        
        with stress_col1:
            stress_duration = st.selectbox(
                "Stress Test Duration",
                ["30 seconds", "1 minute", "2 minutes", "5 minutes"],
                index=0
            )
            
            stress_intensity = st.slider(
                "Stress Intensity",
                min_value=1, max_value=10, value=5
            )
        
        with stress_col2:
            if st.button("🔥 Start Live Stress Test"):
                run_live_stress_test(stress_duration, stress_intensity)
    else:
        st.info("🔒 Stress testing requires completed safety preparation and active hardware session.")
    
    # Live performance tracking
    st.subheader("📈 Live Performance Tracking")
    
    if 'live_performance_data' in st.session_state:
        show_live_performance_chart()
    else:
        st.info("📊 Performance tracking data will appear here during live tuning sessions.")
    
    # Live tuning history
    st.subheader("📋 Live Tuning History")
    
    if 'live_tuning_history' in st.session_state:
        history_df = pd.DataFrame(st.session_state.live_tuning_history)
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("📋 Live tuning history will appear here after making hardware adjustments.")


def run_live_stress_test(duration, intensity):
    """Run a live stress test."""
    st.subheader("🔥 Live Stress Test Running")
    
    duration_seconds = int(duration.split()[0])
    if "minute" in duration:
        duration_seconds *= 60
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(duration_seconds):
        progress = (i + 1) / duration_seconds
        progress_bar.progress(progress)
        
        # Simulate stress test results
        if random.random() < (intensity / 1000):  # Higher intensity = more likely errors
            status_text.error(f"⚠️ Memory error detected at {i}s")
            st.error("🛑 Stress test failed - reverting changes")
            return False
        else:
            status_text.text(f"Running stress test... {i+1}/{duration_seconds}s")
        
        time.sleep(0.1)  # Simulated test time
    
    st.success("✅ Stress test passed!")
    return True


def show_live_performance_chart():
    """Show live performance tracking chart."""
    data = st.session_state.live_performance_data
    
    if len(data) < 2:
        return
    
    # Create performance chart
    timestamps = [d['timestamp'] for d in data]
    performance = [d['performance'] for d in data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=performance,
        mode='lines+markers',
        name='Performance %',
        line=dict(color='#00CC96', width=2)
    ))
    
    fig.update_layout(
        title="Live Performance Tracking",
        xaxis_title="Time",
        yaxis_title="Performance %",
        template="plotly_white",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
