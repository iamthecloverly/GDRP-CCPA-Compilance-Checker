import streamlit as st
from controllers.compliance_controller import ComplianceController
import pandas as pd


st.set_page_config(
    page_title="GDPR/CCPA Compliance Checker",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 GDPR/CCPA Compliance Checker")
st.markdown("Scan websites for privacy compliance gaps including cookie consent, trackers, and privacy policy completeness.")

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    url_input = st.text_input(
        "Enter Website URL",
        placeholder="example.com or https://example.com",
        help="Enter the URL of the website you want to scan for compliance"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    include_ai = st.checkbox("Include AI Analysis", value=True, help="Use OpenAI to analyze privacy policy content")

scan_button = st.button("🔍 Scan Website", type="primary", use_container_width=True)

if scan_button:
    if not url_input:
        st.error("Please enter a website URL to scan.")
    else:
        with st.spinner(f"Scanning {url_input}... This may take a moment."):
            try:
                controller = ComplianceController(url_input)
                results = controller.run_scan(include_ai_analysis=include_ai)
                
                if 'error' in results and not results.get('scan_completed'):
                    st.error(f"❌ Failed to scan website: {results['error']}")
                else:
                    st.success(f"✅ Scan completed for {results.get('url', url_input)}")
                    
                    st.markdown("---")
                    
                    summary = results.get('compliance_summary', {})
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Compliance Score",
                            f"{summary.get('compliance_percentage', 0):.0f}%",
                            delta=summary.get('status', 'Unknown')
                        )
                    
                    with col2:
                        st.metric(
                            "Checks Passed",
                            f"{summary.get('checks_passed', 0)}/{summary.get('total_checks', 4)}"
                        )
                    
                    with col3:
                        status = summary.get('status', 'Unknown')
                        if status == 'Good':
                            st.success(f"Status: {status}")
                        elif status == 'Fair':
                            st.warning(f"Status: {status}")
                        else:
                            st.error(f"Status: {status}")
                    
                    st.markdown("---")
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "🍪 Cookie Banner", "📡 Trackers", "📄 Privacy Policy"])
                    
                    with tab1:
                        st.subheader("Compliance Overview")
                        
                        cookie_banner = results.get('cookie_banner', {})
                        tracking = results.get('tracking_scripts', {})
                        privacy = results.get('privacy_policy', {})
                        contact = results.get('contact_info', {})
                        
                        overview_data = {
                            'Check': [
                                'Cookie Consent Banner',
                                'Privacy Policy',
                                'Contact Information',
                                'Third-Party Trackers'
                            ],
                            'Status': [
                                '✅ Detected' if cookie_banner.get('detected') else '❌ Not Found',
                                '✅ Found' if privacy.get('found') else '❌ Not Found',
                                '✅ Found' if contact.get('detected') else '❌ Not Found',
                                f"⚠️ {tracking.get('total_trackers', 0)} Detected" if tracking.get('total_trackers', 0) > 0 else '✅ None Detected'
                            ],
                            'Details': [
                                f"{cookie_banner.get('banner_elements', 0)} elements, {len(cookie_banner.get('keywords_found', []))} keywords",
                                f"{privacy.get('count', 0)} link(s) found",
                                'Email addresses detected' if contact.get('emails_found') else 'Contact info present',
                                ', '.join(tracking.get('tracker_names', [])[:3]) if tracking.get('tracker_names') else 'No trackers'
                            ]
                        }
                        
                        df = pd.DataFrame(overview_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        if 'recommendations' in results and not results['recommendations'].get('error'):
                            st.markdown("### 🎯 Recommendations")
                            recs = results['recommendations']
                            
                            if recs.get('priority_actions'):
                                st.markdown("**Priority Actions:**")
                                for action in recs['priority_actions']:
                                    st.markdown(f"- {action}")
                            
                            if recs.get('overall_assessment'):
                                st.info(recs['overall_assessment'])
                    
                    with tab2:
                        st.subheader("Cookie Consent Banner Analysis")
                        
                        if cookie_banner.get('detected'):
                            st.success("✅ Cookie consent banner detected")
                            
                            st.markdown("**Keywords Found:**")
                            if cookie_banner.get('keywords_found'):
                                for keyword in cookie_banner['keywords_found']:
                                    st.markdown(f"- {keyword}")
                            
                            st.metric("Banner Elements Detected", cookie_banner.get('banner_elements', 0))
                        else:
                            st.error("❌ No cookie consent banner detected")
                            st.warning("⚠️ GDPR/CCPA requires user consent before setting non-essential cookies. Consider implementing a cookie consent banner.")
                    
                    with tab3:
                        st.subheader("Third-Party Tracking Scripts")
                        
                        total_trackers = tracking.get('total_trackers', 0)
                        
                        if total_trackers > 0:
                            st.warning(f"⚠️ {total_trackers} third-party tracker(s) detected")
                            
                            detected = tracking.get('detected_trackers', {})
                            
                            for tracker_name, scripts in detected.items():
                                with st.expander(f"**{tracker_name}** ({len(scripts)} script(s))"):
                                    for script in scripts[:3]:
                                        st.code(script, language=None)
                            
                            st.info("💡 Ensure users are informed about these trackers in your privacy policy and cookie consent banner.")
                        else:
                            st.success("✅ No third-party trackers detected")
                        
                        st.metric("Total Scripts on Page", tracking.get('total_scripts', 0))
                    
                    with tab4:
                        st.subheader("Privacy Policy Analysis")
                        
                        if privacy.get('found'):
                            st.success(f"✅ {privacy.get('count', 0)} privacy policy link(s) found")
                            
                            st.markdown("**Privacy Policy Links:**")
                            for link in privacy.get('links', []):
                                st.markdown(f"- [{link['text']}]({link['url']})")
                            
                            if 'policy_analysis' in results and not results['policy_analysis'].get('error'):
                                st.markdown("---")
                                st.markdown("### 🤖 AI-Powered Policy Analysis")
                                
                                analysis = results['policy_analysis']
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    gdpr_status = "✅ Compliant" if analysis.get('gdpr_compliant') else "❌ Non-Compliant"
                                    st.metric("GDPR", gdpr_status)
                                
                                with col2:
                                    ccpa_status = "✅ Compliant" if analysis.get('ccpa_compliant') else "❌ Non-Compliant"
                                    st.metric("CCPA", ccpa_status)
                                
                                with col3:
                                    st.metric("Compliance Score", f"{analysis.get('overall_compliance_score', 0)}%")
                                
                                st.markdown("---")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**✅ Compliance Strengths:**")
                                    strengths = analysis.get('strengths', [])
                                    if strengths:
                                        for strength in strengths:
                                            st.markdown(f"- {strength}")
                                    else:
                                        st.markdown("- None identified")
                                
                                with col2:
                                    st.markdown("**❌ Missing Elements:**")
                                    missing = analysis.get('missing_elements', [])
                                    if missing:
                                        for item in missing:
                                            st.markdown(f"- {item}")
                                    else:
                                        st.markdown("- None")
                                
                                st.markdown("---")
                                st.markdown("**Summary:**")
                                st.info(analysis.get('summary', 'No summary available'))
                                
                                compliance_items = {
                                    'Data Collection Mentioned': analysis.get('data_collection_mentioned', False),
                                    'Data Deletion Rights': analysis.get('data_deletion_rights', False),
                                    'Data Sharing Disclosed': analysis.get('data_sharing_disclosed', False),
                                    'User Consent Mechanism': analysis.get('user_consent_mechanism', False),
                                    'Contact Information': analysis.get('contact_information_provided', False),
                                    'Cookie Usage Explained': analysis.get('cookie_usage_explained', False),
                                    'Third-Party Disclosure': analysis.get('third_party_disclosure', False)
                                }
                                
                                st.markdown("**Detailed Compliance Checklist:**")
                                checklist_df = pd.DataFrame([
                                    {'Item': key, 'Status': '✅ Yes' if value else '❌ No'}
                                    for key, value in compliance_items.items()
                                ])
                                st.dataframe(checklist_df, use_container_width=True, hide_index=True)
                                
                            elif results.get('policy_analysis', {}).get('error'):
                                st.warning(f"⚠️ {results['policy_analysis']['error']}")
                        else:
                            st.error("❌ No privacy policy found")
                            st.warning("⚠️ GDPR/CCPA requires a clear and accessible privacy policy. Add a privacy policy link to your website footer or header.")
                    
            except Exception as e:
                st.error(f"❌ An error occurred during scanning: {str(e)}")
                st.exception(e)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>GDPR/CCPA Compliance Checker</strong></p>
        <p style='font-size: 0.9em;'>This tool provides a preliminary compliance assessment. For legal compliance verification, consult with a privacy attorney.</p>
    </div>
    """,
    unsafe_allow_html=True
)
