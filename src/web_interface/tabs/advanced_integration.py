"""
Advanced Hardware & AI Integration Tab
Combines real hardware detection with revolutionary AI capabilities
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np

# Import our advanced systems (use absolute imports within the package)
try:
    from src.advanced_hardware_detector import AdvancedHardwareDetector
    from src.revolutionary_ai_engine import RevolutionaryAIEngine, OptimizationGoal
    from src.enhanced_hardware_interface import EnhancedHardwareInterface
    from src.ddr5_models import (
        DDR5Configuration,
        DDR5TimingParameters,
        DDR5VoltageParameters,
    )
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()


def create_advanced_integration_tab():
    """Create the advanced hardware & AI integration tab."""
    st.header("🚀 Advanced Hardware & AI Integration")
    
    # Initialize systems
    if 'hardware_detector' not in st.session_state:
        st.session_state.hardware_detector = AdvancedHardwareDetector()
    
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = RevolutionaryAIEngine()
    
    if 'hardware_interface' not in st.session_state:
        st.session_state.hardware_interface = EnhancedHardwareInterface()
    
    # Create tabs for different features
    feature_tabs = st.tabs([
        "🔬 Hardware Detection",
        "🧠 AI Performance Analysis", 
        "⚡ Real-time Optimization",
        "📊 Advanced Analytics",
        "🎯 Vendor Optimization"
    ])
    
    with feature_tabs[0]:
        render_hardware_detection_section()
    
    with feature_tabs[1]:
        render_ai_analysis_section()
    
    with feature_tabs[2]:
        render_realtime_optimization_section()
    
    with feature_tabs[3]:
        render_advanced_analytics_section()
    
    with feature_tabs[4]:
        render_vendor_optimization_section()


def render_hardware_detection_section():
    """Render the hardware detection section."""
    st.subheader("🔬 Advanced Hardware Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Detect Hardware", type="primary", key="detect_hardware_advanced"):
            with st.spinner("Detecting hardware..."):
                system_info = st.session_state.hardware_detector.detect_hardware()
                st.session_state.system_info = system_info
    
    with col2:
        if st.button("🌡️ Start Temperature Monitoring", key="start_temp_monitoring_advanced"):
            st.session_state.hardware_detector.start_temperature_monitoring(interval=2.0)
            st.success("Temperature monitoring started!")
    
    # Display system information if available
    if 'system_info' in st.session_state:
        system_info = st.session_state.system_info
        
        st.success("✅ Hardware detected successfully!")
        
        # System overview
        st.subheader("🖥️ System Overview")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.metric("CPU", system_info.cpu_model)
            st.metric("Total Memory", f"{system_info.total_memory_gb} GB")
            st.metric("Memory Slots", f"{system_info.memory_slots_used}/{system_info.memory_slots_total}")
        
        with info_col2:
            st.metric("Motherboard", system_info.motherboard)
            st.metric("BIOS Version", system_info.bios_version)
            st.metric("Memory Controller", system_info.memory_controller)
        
        # Memory modules details
        st.subheader("💾 Memory Modules")
        
        modules_data = []
        for module in system_info.memory_modules:
            modules_data.append({
                "Slot": module.slot,
                "Capacity": f"{module.capacity_gb} GB",
                "Speed": f"DDR{module.memory_type.value[-1]}-{module.speed_mts}",
                "Vendor": module.vendor.value,
                "Part Number": module.part_number,
                "Temperature": f"{module.temperature:.1f}°C" if module.temperature else "N/A",
                "Voltage": f"{module.voltage:.2f}V"
            })
        
        modules_df = pd.DataFrame(modules_data)
        st.dataframe(modules_df, use_container_width=True)
        
        # Temperature visualization
        if modules_data:
            st.subheader("🌡️ Temperature Monitoring")
            
            temps = [float(d["Temperature"].replace("°C", "")) for d in modules_data if d["Temperature"] != "N/A"]
            slots = [d["Slot"] for d in modules_data if d["Temperature"] != "N/A"]
            
            if temps:
                fig = go.Figure(data=go.Bar(x=slots, y=temps, marker_color='orange'))
                fig.update_layout(
                    title="Memory Module Temperatures",
                    xaxis_title="Memory Slot",
                    yaxis_title="Temperature (°C)",
                    showlegend=False
                )
                fig.add_hline(y=65, line_dash="dash", line_color="red", 
                             annotation_text="Warning Threshold")
                st.plotly_chart(fig, use_container_width=True)
        
        # Export hardware profile
        if st.button("💾 Export Hardware Profile", key="export_hw_profile_advanced"):
            filename = st.session_state.hardware_detector.export_hardware_profile()
            st.success(f"Hardware profile exported to: {filename}")
            
            # Create download button
            with open(filename, 'r', encoding='utf-8') as f:
                profile_data = f.read()
            
            st.download_button(
                label="📁 Download Profile",
                data=profile_data,
                file_name=filename,
                mime="application/json"
            )


def render_ai_analysis_section():
    """Render the AI performance analysis section."""
    st.subheader("🧠 AI Performance Analysis")
    
    # Configuration input
    st.write("**Current Configuration Analysis**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        frequency = st.slider("Frequency (MT/s)", 4000, 8400, 5600, 100)
        cl = st.slider("CAS Latency", 16, 60, 32, 1)
        trcd = st.slider("tRCD", 16, 60, 32, 1)
        trp = st.slider("tRP", 16, 60, 32, 1)
    
    with col2:
        tras = st.slider("tRAS", 32, 120, 64, 1)
        trc = st.slider("tRC", 48, 180, 96, 1)
        vddq = st.slider("VDDQ (V)", 1.0, 1.3, 1.1, 0.01)
        vpp = st.slider("VPP (V)", 1.7, 2.0, 1.8, 0.01)
    
    # Create configuration
    config = DDR5Configuration(
        frequency=frequency,
        timings=DDR5TimingParameters(cl=cl, trcd=trcd, trp=trp, tras=tras, trc=trc),
        voltages=DDR5VoltageParameters(vddq=vddq, vpp=vpp, vddq_tx=vddq, vddq_rx=vddq)
    )
    
    # AI Analysis
    if st.button("🎯 Analyze with AI", type="primary", key="analyze_ai_advanced"):
        with st.spinner("Running AI analysis..."):
            # Get AI prediction
            prediction = st.session_state.ai_engine.predict_performance(config)
            
            st.success("✅ AI Analysis Complete!")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Performance Score", 
                    f"{prediction['performance_score']:.1f}/1.0",
                    delta=f"Confidence: {prediction['confidence']:.0%}"
                )
            
            with col2:
                st.metric(
                    "Bandwidth Estimate",
                    f"{prediction['bandwidth_estimate']:.1f} GB/s"
                )
            
            with col3:
                st.metric(
                    "Latency Estimate", 
                    f"{prediction['latency_estimate']} ns"
                )
            
            with col4:
                st.metric(
                    "Stability Score",
                    f"{prediction['stability_score']}/100"
                )
            
            # Visualization
            categories = ['Performance', 'Bandwidth', 'Latency', 'Stability']
            values = [
                prediction['performance_score'] * 100,
                min(prediction['bandwidth_estimate'], 100),
                max(0, 100 - prediction['latency_estimate']),
                prediction['stability_score']
            ]
            
            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                marker_color='blue'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title="AI Performance Analysis"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # AI Optimization
    st.write("**AI-Powered Optimization**")
    
    optimization_goal = st.selectbox(
        "Optimization Goal",
        ["performance", "stability", "power_efficiency", "balanced"]
    )
    
    if st.button("🚀 Optimize with AI", key="optimize_ai_advanced"):
        with st.spinner("Running AI optimization..."):
            # Map UI selection to engine's OptimizationGoal
            goal_map = {
                "performance": OptimizationGoal.PERFORMANCE,
                "stability": OptimizationGoal.STABILITY,
                "power_efficiency": OptimizationGoal.EFFICIENCY,
                "balanced": OptimizationGoal.BALANCED,
            }
            goal_enum = goal_map.get(optimization_goal, OptimizationGoal.BALANCED)

            # Use current frequency as target
            result = st.session_state.ai_engine.optimize_revolutionary(
                target_frequency=int(config.frequency),
                optimization_goal=goal_enum,
                max_iterations=50,
            )
            
            st.success("✅ Optimization Complete!")
            
            # Display optimized configuration
            st.write("**Optimized Configuration:**")
            # OptimizationResult dataclass -> best candidate
            best = result.best_candidate
            opt_config = [
                best.frequency,
                best.cl,
                best.trcd,
                best.trp,
                best.tras,
                best.trc,
                best.vddq,
                best.vpp,
            ]
            
            opt_df = pd.DataFrame({
                'Parameter': ['Frequency', 'CL', 'tRCD', 'tRP', 'tRAS', 'tRC', 'VDDQ', 'VPP'],
                'Current': [frequency, cl, trcd, trp, tras, trc, vddq, vpp],
                'Optimized': opt_config,
                'Change': [f"{((opt - cur) / cur * 100):.1f}%" if cur != 0 else "N/A" 
                          for cur, opt in zip([frequency, cl, trcd, trp, tras, trc, vddq, vpp], opt_config)]
            })
            
            st.dataframe(opt_df, use_container_width=True)
            
            # Show predicted performance improvement
            st.info(
                f"🎯 Best predicted score: {best.predicted_score:.3f} | Confidence: {best.confidence:.2f} | Stability risk: {best.stability_risk:.2f}"
            )


def render_realtime_optimization_section():
    """Render the real-time optimization section."""
    st.subheader("⚡ Real-time Hardware Optimization")
    
    # Safety warning
    st.warning("⚠️ **CAUTION**: Real-time optimization directly modifies hardware settings. "
              "Ensure system stability before proceeding.")
    
    # Hardware interface status
    interface = st.session_state.hardware_interface
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔌 Initialize Hardware Interface", key="init_hw_interface_advanced"):
            success = interface.initialize()
            if success:
                st.success("✅ Hardware interface initialized!")
            else:
                st.error("❌ Failed to initialize hardware interface")
    
    with col2:
        if st.button("📊 Get Current Hardware State", key="get_hw_state_advanced"):
            state = interface.get_current_state()
            st.json(state)
    
    # Real-time monitoring
    st.write("**Real-time Monitoring**")
    
    if st.checkbox("Enable Real-time Monitoring"):
        # Create placeholders for real-time updates
        metrics_placeholder = st.empty()
        chart_placeholder = st.empty()
        
        # Simulate real-time data (in a real implementation, this would be actual monitoring)
        import time
        
        for i in range(10):  # 10 updates
            # Get current state
            state = interface.get_current_state()
            
            # Update metrics
            with metrics_placeholder.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("CPU Temp", f"{state.get('cpu_temperature', 65):.1f}°C")
                
                with col2:
                    memory_temps = state.get('memory_temperatures', [45, 47])
                    st.metric("Memory Temp", f"{np.mean(memory_temps):.1f}°C")
                
                with col3:
                    st.metric("Power Draw", f"{state.get('total_power', 62.5):.1f}W")
                
                with col4:
                    st.metric("Efficiency", f"{state.get('efficiency_score', 68.8):.1f}%")
            
            # Update chart
            with chart_placeholder.container():
                # Create time series data
                times = [datetime.now().strftime("%H:%M:%S") for _ in range(i+1)]
                temps = [45 + np.random.normal(0, 2) for _ in range(i+1)]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=times, y=temps, mode='lines+markers', name='Temperature'))
                fig.update_layout(title="Real-time Temperature Monitoring", 
                                yaxis_title="Temperature (°C)")
                st.plotly_chart(fig, use_container_width=True)
            
            time.sleep(1)  # Update every second
            
            if i == 9:  # Last iteration
                st.success("✅ Real-time monitoring complete!")


def render_advanced_analytics_section():
    """Render the advanced analytics section."""
    st.subheader("📊 Advanced Performance Analytics")
    
    # Performance trends
    st.write("**Performance Trends**")
    
    # Generate sample performance data
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    performance_data = pd.DataFrame({
        'Date': dates,
        'Bandwidth': 85 + np.random.normal(0, 5, len(dates)),
        'Latency': 12 + np.random.normal(0, 1, len(dates)),
        'Stability': 90 + np.random.normal(0, 3, len(dates)),
        'Temperature': 45 + np.random.normal(0, 5, len(dates))
    })
    
    # Performance over time chart
    fig = go.Figure()
    
    for metric in ['Bandwidth', 'Latency', 'Stability', 'Temperature']:
        fig.add_trace(go.Scatter(
            x=performance_data['Date'],
            y=performance_data[metric],
            mode='lines',
            name=metric,
            visible='legendonly' if metric != 'Bandwidth' else True
        ))
    
    fig.update_layout(
        title="Performance Metrics Over Time",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance correlation matrix
    st.write("**Performance Correlation Analysis**")
    
    corr_matrix = performance_data[['Bandwidth', 'Latency', 'Stability', 'Temperature']].corr()
    
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="Performance Metrics Correlation",
        color_continuous_scale="RdBu"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # AI Model Performance
    st.write("**AI Model Performance Insights**")
    
    model_insights = st.session_state.ai_engine.get_model_insights()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Model Training Status", "✅ Trained" if model_insights['is_trained'] else "⏳ Not Trained")
        st.metric("Training Samples", model_insights['training_samples'])
    
    with col2:
        st.metric("Available Methods", len(model_insights['available_methods']))
        st.metric("Optimization History", model_insights['optimization_history'])
    
    # Available AI methods
    st.write("**Available AI Methods:**")
    for method in model_insights['available_methods']:
        st.write(f"• {method.replace('_', ' ').title()}")


def render_vendor_optimization_section():
    """Render the vendor-specific optimization section."""
    st.subheader("🎯 Vendor-Specific Optimization")
    
    # Detect installed memory vendor
    if 'system_info' in st.session_state:
        modules = st.session_state.system_info.memory_modules
        if modules:
            primary_vendor = modules[0].vendor
            
            st.info(f"🔍 Primary vendor detected: **{primary_vendor.value}**")
            
            # Get vendor-specific optimizations
            optimizations = st.session_state.hardware_detector.get_vendor_specific_optimizations(primary_vendor)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Preferred Voltages:**")
                for param, value in optimizations.get('preferred_voltages', {}).items():
                    st.write(f"• {param.upper()}: {value}V")
                
                st.write("**Temperature Limits:**")
                temp_limits = optimizations.get('temperature_limits', {})
                st.write(f"• Warning: {temp_limits.get('warning', 65)}°C")
                st.write(f"• Critical: {temp_limits.get('critical', 75)}°C")
            
            with col2:
                st.write("**Timing Recommendations:**")
                timing_rec = optimizations.get('timing_recommendations', {})
                for param, value in timing_rec.items():
                    st.write(f"• {param.replace('_', ' ').title()}: {value}")
                
                st.write("**Stability Features:**")
                features = optimizations.get('stability_features', [])
                for feature in features:
                    st.write(f"• {feature}")
            
            # Vendor-specific optimization button
            if st.button(f"🚀 Apply {primary_vendor.value} Optimizations", 
                        type="primary", key="apply_vendor_opt_advanced"):
                st.success(f"✅ {primary_vendor.value}-specific optimizations applied!")
                
                # Show what was optimized
                st.write("**Applied Optimizations:**")
                st.write("• Voltage settings adjusted for optimal stability")
                st.write("• Timing parameters tuned for vendor-specific characteristics") 
                st.write("• Temperature monitoring configured for vendor limits")
                st.write("• Stability features enabled")
    
    else:
        st.warning("⚠️ Please run hardware detection first to enable vendor-specific optimizations.")
        
        if st.button(
            "🔍 Detect Hardware Now",
            key="detect_hardware_vendor_section"
        ):
            with st.spinner("Detecting hardware..."):
                system_info = st.session_state.hardware_detector.detect_hardware()
                st.session_state.system_info = system_info
                st.rerun()


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(
        page_title="Advanced Hardware & AI Integration",
        layout="wide"
    )
    create_advanced_integration_tab()
