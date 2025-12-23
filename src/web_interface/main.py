"""
Main web interface entry point.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure repository root is on sys.path when running as a script (e.g., streamlit run src/web_interface/main.py)
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.web_interface.utils.session_state import initialize_session_state
from src.web_interface.sidebar import render_sidebar
from src.web_interface.tabs.manual_tuning import render_manual_tuning_tab
from src.web_interface.tabs.simulation import render_simulation_tab
from src.web_interface.tabs.ai_optimization import render_ai_optimization_tab
from src.web_interface.tabs.gaming import render_gaming_tab
from src.web_interface.tabs.analysis import render_analysis_tab
from src.web_interface.tabs.benchmarks import render_benchmarks_tab
from src.web_interface.tabs.hardware_detection import render_hardware_detection_tab
from src.web_interface.tabs.live_tuning import render_live_tuning_tab
from src.web_interface.tabs.cross_brand_tuning import render_cross_brand_tuning_tab
from src.web_interface.tabs.enhanced_features_v2 import render_enhanced_features_tab
from src.web_interface.tabs.advanced_integration import create_advanced_integration_tab


def create_perfect_web_interface():
    """Create the main web interface."""
    # Page configuration
    st.set_page_config(
        page_title="Perfect DDR5 AI Optimizer",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()

    # Main title with styling
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🧠 Perfect DDR5 AI Optimizer</h1>
        <h3>Ultimate AI-Powered Memory Tuning Without Hardware</h3>
        <p style='color: #666;'>Advanced ML • Quantum Optimization • Molecular Analysis • Revolutionary Features</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ko-fi donation button (prominent and clickable)
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        if st.button("☕ Support Development on Ko-fi", 
                    type="primary", use_container_width=True):
            st.balloons()
            st.markdown("""
            <div style='text-align: center; margin: 20px 0;'>
                <a href="https://ko-fi.com/killerbotofthenewworld" target="_blank" 
                   style='background: #FF5E5B; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; 
                          display: inline-block; font-size: 16px;'>
                    ☕ Open Ko-fi in New Tab
                </a>
            </div>
            <p style='text-align: center; color: #888; font-size: 14px;'>
                💖 Support continued development of revolutionary AI features!
            </p>
            """, unsafe_allow_html=True)

    # Render sidebar and get configuration
    config, _ = render_sidebar()

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "⚙️ Manual Tuning",
        "⚡ Simulation",
        "🧠 AI Optimization",
        "🎮 Gaming Performance",
        "📊 Analysis",
        "🚀 Enhanced Features",
        "📈 Benchmarks",
        "💻 Hardware Detection",
        "⚡ Live Tuning",
        "🔄 Cross-Brand Tuning",
        "🔬 Advanced Integration"
    ])

    # Render each tab with full functionality
    with tab1:
        render_manual_tuning_tab(config)

    with tab2:
        render_simulation_tab(config)

    with tab3:
        render_ai_optimization_tab()
    
    with tab4:
        render_gaming_tab(config)
    
    with tab5:
        render_analysis_tab()
    
    with tab6:
        render_enhanced_features_tab()
    
    with tab7:
        render_benchmarks_tab(config)
    
    with tab8:
        render_hardware_detection_tab()
    
    with tab9:
        render_live_tuning_tab(config)
    
    with tab10:
        render_cross_brand_tuning_tab(config)
    
    with tab11:
        create_advanced_integration_tab()


if __name__ == "__main__":
    create_perfect_web_interface()
