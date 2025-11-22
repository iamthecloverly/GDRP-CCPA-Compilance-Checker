import streamlit as st
from controllers.compliance_controller import ComplianceController
import numpy as np
from datetime import datetime
import json
from io import StringIO
import csv
from database.db import init_db
from database.operations import save_scan_result, get_scan_history, get_score_trend, get_all_scanned_urls

init_db()


def _generate_csv_export(results: dict, scan_time: str) -> str:
    csv_buffer = StringIO()
    
    csv_buffer.write("GDPR/CCPA Compliance Report\n")
    csv_buffer.write(f"Scan Date,{scan_time}\n")
    csv_buffer.write(f"Website URL,{results.get('url', 'N/A')}\n")
    csv_buffer.write("\n")
    
    summary = results.get('compliance_summary', {})
    csv_buffer.write("Overall Compliance Summary\n")
    csv_buffer.write(f"Overall Score,{summary.get('weighted_score', 0):.1f}/100\n")
    csv_buffer.write(f"Grade,{summary.get('grade', 'N/A')}\n")
    csv_buffer.write(f"Status,{summary.get('status', 'Unknown')}\n")
    csv_buffer.write("\n")
    
    csv_buffer.write("Category Scores\n")
    csv_buffer.write("Category,Score,Weight,Weighted Score\n")
    category_scores = summary.get('category_scores', {})
    weights = summary.get('weights', {})
    csv_buffer.write(f"Cookie Consent,{category_scores.get('cookie_consent', 0)}/100,{weights.get('cookie_consent', 0)*100:.0f}%,{category_scores.get('cookie_consent', 0) * weights.get('cookie_consent', 0):.1f}\n")
    csv_buffer.write(f"Privacy Policy,{category_scores.get('privacy_policy', 0)}/100,{weights.get('privacy_policy', 0)*100:.0f}%,{category_scores.get('privacy_policy', 0) * weights.get('privacy_policy', 0):.1f}\n")
    csv_buffer.write(f"Tracker Management,{category_scores.get('trackers', 0)}/100,{weights.get('trackers', 0)*100:.0f}%,{category_scores.get('trackers', 0) * weights.get('trackers', 0):.1f}\n")
    csv_buffer.write(f"Contact Information,{category_scores.get('contact_info', 0)}/100,{weights.get('contact_info', 0)*100:.0f}%,{category_scores.get('contact_info', 0) * weights.get('contact_info', 0):.1f}\n")
    csv_buffer.write("\n")
    
    cookie_banner = results.get('cookie_banner', {})
    csv_buffer.write("Cookie Banner Detection\n")
    csv_buffer.write(f"Detected,{cookie_banner.get('detected', False)}\n")
    csv_buffer.write(f"Banner Elements,{cookie_banner.get('banner_elements', 0)}\n")
    csv_buffer.write(f"Keywords Found,\"{', '.join(cookie_banner.get('keywords_found', []))}\"\n")
    csv_buffer.write("\n")
    
    tracking = results.get('tracking_scripts', {})
    csv_buffer.write("Tracking Scripts\n")
    csv_buffer.write(f"Total Trackers Detected,{tracking.get('total_trackers', 0)}\n")
    csv_buffer.write(f"Total Scripts,{tracking.get('total_scripts', 0)}\n")
    csv_buffer.write(f"Tracker Names,\"{', '.join(tracking.get('tracker_names', []))}\"\n")
    csv_buffer.write("\n")
    
    privacy = results.get('privacy_policy', {})
    csv_buffer.write("Privacy Policy\n")
    csv_buffer.write(f"Found,{privacy.get('found', False)}\n")
    csv_buffer.write(f"Link Count,{privacy.get('count', 0)}\n")
    csv_buffer.write("\n")
    
    if 'policy_analysis' in results and not results['policy_analysis'].get('error'):
        analysis = results['policy_analysis']
        csv_buffer.write("AI Policy Analysis\n")
        csv_buffer.write(f"GDPR Compliant,{analysis.get('gdpr_compliant', False)}\n")
        csv_buffer.write(f"CCPA Compliant,{analysis.get('ccpa_compliant', False)}\n")
        csv_buffer.write(f"AI Compliance Score,{analysis.get('overall_compliance_score', 0)}%\n")
        csv_buffer.write(f"Data Collection Mentioned,{analysis.get('data_collection_mentioned', False)}\n")
        csv_buffer.write(f"Data Deletion Rights,{analysis.get('data_deletion_rights', False)}\n")
        csv_buffer.write(f"Data Sharing Disclosed,{analysis.get('data_sharing_disclosed', False)}\n")
        csv_buffer.write(f"User Consent Mechanism,{analysis.get('user_consent_mechanism', False)}\n")
        csv_buffer.write(f"Cookie Usage Explained,{analysis.get('cookie_usage_explained', False)}\n")
        csv_buffer.write(f"Third Party Disclosure,{analysis.get('third_party_disclosure', False)}\n")
        csv_buffer.write("\n")
    
    if 'recommendations' in results and not results['recommendations'].get('error'):
        recs = results['recommendations']
        csv_buffer.write("Priority Actions\n")
        for i, action in enumerate(recs.get('priority_actions', []), 1):
            csv_buffer.write(f"{i},\"{action}\"\n")
        csv_buffer.write("\n")
    
    return csv_buffer.getvalue()


st.set_page_config(
    page_title="GDPR/CCPA Compliance Checker",
    page_icon="🔒",
    layout="wide"
)

# Hide Streamlit branding
hide_streamlit_style = """
    <style>
    #MainMenu {display: none;}
    footer {display: none;}
    header {display: none;}
    .stDeployButton {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🔒 GDPR/CCPA Compliance Checker")
st.markdown("Scan websites for privacy compliance gaps including cookie consent, trackers, and privacy policy completeness.")

st.markdown("---")

tab_scan, tab_history, tab_batch = st.tabs(["🔍 Single Scan", "📊 Scan History", "📦 Batch Scan"])

with tab_scan:
    col1, col2 = st.columns([2, 1])

    with col1:
        url_input = st.text_input(
            "Enter Website URL",
            placeholder="example.com or https://example.com",
            help="Enter the URL of the website you want to scan for compliance"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        include_ai = st.checkbox("Include AI Analysis", value=False, help="Use OpenAI to analyze privacy policy content")

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
                        scan_id = save_scan_result(results)
                        st.success(f"✅ Scan completed for {results.get('url', url_input)}")
                        
                        st.markdown("---")
                        
                        summary = results.get('compliance_summary', {})
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Overall Score",
                                f"{summary.get('weighted_score', 0):.1f}/100",
                                delta=summary.get('status', 'Unknown')
                            )
                        
                        with col2:
                            grade = summary.get('grade', 'N/A')
                            grade_color = summary.get('color', 'gray')
                            st.markdown(f"### Grade: <span style='color:{grade_color}; font-size:2em'>{grade}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            status = summary.get('status', 'Unknown')
                            if status in ['Excellent', 'Good']:
                                st.success(f"Status: {status}")
                            elif status == 'Fair':
                                st.warning(f"Status: {status}")
                            else:
                                st.error(f"Status: {status}")
                        
                        with col4:
                            scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            csv_data = _generate_csv_export(results, scan_time)
                            st.download_button(
                                label="📥 Download CSV Report",
                                data=csv_data,
                                file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        
                        category_scores = summary.get('category_scores', {})
                        weights = summary.get('weights', {})
                        
                        st.markdown("### Category Breakdown")
                        score_data = [
                            {
                                'Category': 'Cookie Consent Banner',
                                'Score': f"{category_scores.get('cookie_consent', 0)}/100",
                                'Weight': f"{weights.get('cookie_consent', 0)*100:.0f}%",
                                'Weighted Score': f"{category_scores.get('cookie_consent', 0) * weights.get('cookie_consent', 0):.1f}"
                            },
                            {
                                'Category': 'Privacy Policy',
                                'Score': f"{category_scores.get('privacy_policy', 0)}/100",
                                'Weight': f"{weights.get('privacy_policy', 0)*100:.0f}%",
                                'Weighted Score': f"{category_scores.get('privacy_policy', 0) * weights.get('privacy_policy', 0):.1f}"
                            },
                            {
                                'Category': 'Tracker Management',
                                'Score': f"{category_scores.get('trackers', 0)}/100",
                                'Weight': f"{weights.get('trackers', 0)*100:.0f}%",
                                'Weighted Score': f"{category_scores.get('trackers', 0) * weights.get('trackers', 0):.1f}"
                            },
                            {
                                'Category': 'Contact Information',
                                'Score': f"{category_scores.get('contact_info', 0)}/100",
                                'Weight': f"{weights.get('contact_info', 0)*100:.0f}%",
                                'Weighted Score': f"{category_scores.get('contact_info', 0) * weights.get('contact_info', 0):.1f}"
                            }
                        ]
                        st.dataframe(score_data, use_container_width=True, hide_index=True)
                        
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
                            
                            st.dataframe(overview_data, use_container_width=True, hide_index=True)
                            
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
                                    checklist_data = [
                                        {'Item': key, 'Status': '✅ Yes' if value else '❌ No'}
                                        for key, value in compliance_items.items()
                                    ]
                                    st.dataframe(checklist_data, use_container_width=True, hide_index=True)
                                    
                                elif results.get('policy_analysis', {}).get('error'):
                                    st.warning(f"⚠️ {results['policy_analysis']['error']}")
                            else:
                                st.error("❌ No privacy policy found")
                                st.warning("⚠️ GDPR/CCPA requires a clear and accessible privacy policy. Add a privacy policy link to your website footer or header.")
                        
                except Exception as e:
                        st.error(f"❌ An error occurred during scanning: {str(e)}")
                        st.exception(e)

with tab_history:
    st.subheader("📊 Scan History & Trends")
    
    scanned_urls = get_all_scanned_urls()
    
    if not scanned_urls:
        st.info("No scan history available yet. Scan a website to start tracking compliance over time.")
    else:
        selected_url = st.selectbox("Select a website to view history:", scanned_urls)
        
        if selected_url:
            history = get_scan_history(selected_url, limit=20)
            trend_data = get_score_trend(selected_url, limit=20)
            
            if history:
                st.markdown(f"### History for: **{selected_url}**")
                st.markdown(f"Total scans: **{len(history)}**")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Compliance Score Trend")
                    if trend_data['dates'] and len(trend_data['dates']) > 0:
                        chart_data = {
                            'Date': [datetime.fromisoformat(d) for d in trend_data['dates']],
                            'Overall Score': trend_data['scores']
                        }
                        st.line_chart(chart_data, x='Date', y='Overall Score')
                    else:
                        st.info("No trend data available yet. Scan this website multiple times to see trends.")
                
                with col2:
                    st.markdown("#### Category Scores Trend")
                    if trend_data['dates'] and len(trend_data['dates']) > 0:
                        category_chart_data = {
                            'Date': [datetime.fromisoformat(d) for d in trend_data['dates']],
                            'Cookie': trend_data['cookie_scores'],
                            'Privacy': trend_data['privacy_scores'],
                            'Trackers': trend_data['tracker_scores']
                        }
                        st.line_chart(category_chart_data, x='Date', y=['Cookie', 'Privacy', 'Trackers'])
                    else:
                        st.info("No trend data available yet. Scan this website multiple times to see trends.")
                
                st.markdown("---")
                st.markdown("#### Scan History Table")
                
                history_data = [
                    {
                        'Date': datetime.fromisoformat(scan['scan_date']).strftime('%Y-%m-%d %H:%M'),
                        'Score': f"{scan['overall_score']:.1f}",
                        'Grade': scan['grade'],
                        'Status': scan['status'],
                        'Cookie Banner': '✅' if scan['cookie_banner_detected'] else '❌',
                        'Privacy Policy': '✅' if scan['privacy_policy_found'] else '❌',
                        'Trackers': scan['total_trackers'],
                        'GDPR': '✅' if scan['gdpr_compliant'] else ('❌' if scan['gdpr_compliant'] is not None else 'N/A'),
                        'CCPA': '✅' if scan['ccpa_compliant'] else ('❌' if scan['ccpa_compliant'] is not None else 'N/A')
                    }
                    for scan in history
                ]
                
                st.dataframe(history_data, use_container_width=True, hide_index=True)
                
                if len(history) >= 2:
                    latest = history[0]
                    previous = history[1]
                    score_change = latest['overall_score'] - previous['overall_score']
                    
                    st.markdown("#### Recent Changes")
                    if score_change > 0:
                        st.success(f"📈 Score improved by {score_change:.1f} points since last scan!")
                    elif score_change < 0:
                        st.error(f"📉 Score decreased by {abs(score_change):.1f} points since last scan.")
                    else:
                        st.info("➡️ Score unchanged since last scan.")

with tab_batch:
    st.subheader("📦 Batch Scan Multiple Websites")
    st.markdown("Enter multiple URLs (one per line) to scan them all at once and compare compliance.")
    
    batch_urls = st.text_area(
        "URLs to scan:",
        placeholder="example1.com\nexample2.com\nexample3.com",
        height=150
    )
    
    batch_include_ai = st.checkbox("Include AI Analysis (slower)", value=False, key="batch_ai", 
                                   help="AI analysis significantly increases scan time for batch operations")
    
    batch_scan_button = st.button("🔍 Scan All Websites", type="primary", use_container_width=True, key="batch_scan")
    
    if batch_scan_button:
        if not batch_urls.strip():
            st.error("Please enter at least one URL to scan.")
        else:
            urls_list = [url.strip() for url in batch_urls.split('\n') if url.strip()]
            
            if len(urls_list) > 10:
                st.warning("⚠️ Batch scanning is limited to 10 URLs at a time to prevent timeouts.")
                urls_list = urls_list[:10]
            
            st.info(f"Scanning {len(urls_list)} website(s)...")
            
            batch_results = []
            progress_bar = st.progress(0)
            
            for idx, url in enumerate(urls_list):
                with st.spinner(f"Scanning {url} ({idx+1}/{len(urls_list)})..."):
                    try:
                        controller = ComplianceController(url)
                        result = controller.run_scan(include_ai_analysis=batch_include_ai)
                        
                        if not ('error' in result and not result.get('scan_completed')):
                            save_scan_result(result)
                            batch_results.append(result)
                        else:
                            st.warning(f"⚠️ Failed to scan {url}: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.warning(f"⚠️ Error scanning {url}: {str(e)}")
                
                progress_bar.progress((idx + 1) / len(urls_list))
            
            if batch_results:
                st.success(f"✅ Successfully scanned {len(batch_results)} website(s)!")
                
                st.markdown("---")
                st.markdown("### Batch Scan Results Comparison")
                
                comparison_data = [
                    {
                        'Website': result.get('url', 'N/A'),
                        'Score': f"{result.get('compliance_summary', {}).get('weighted_score', 0):.1f}",
                        'Grade': result.get('compliance_summary', {}).get('grade', 'N/A'),
                        'Status': result.get('compliance_summary', {}).get('status', 'Unknown'),
                        'Cookie Banner': '✅' if result.get('cookie_banner', {}).get('detected') else '❌',
                        'Privacy Policy': '✅' if result.get('privacy_policy', {}).get('found') else '❌',
                        'Trackers': result.get('tracking_scripts', {}).get('total_trackers', 0),
                        'Contact Info': '✅' if result.get('contact_info', {}).get('detected') else '❌'
                    }
                    for result in batch_results
                ]
                
                st.dataframe(comparison_data, use_container_width=True, hide_index=True)
                
                avg_score = sum(r.get('compliance_summary', {}).get('weighted_score', 0) for r in batch_results) / len(batch_results)
                total_trackers = sum(r.get('tracking_scripts', {}).get('total_trackers', 0) for r in batch_results)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Score", f"{avg_score:.1f}/100")
                with col2:
                    st.metric("Total Trackers Found", total_trackers)
                with col3:
                    compliant_count = sum(1 for r in batch_results if r.get('compliance_summary', {}).get('weighted_score', 0) >= 65)
                    st.metric("Compliant Sites", f"{compliant_count}/{len(batch_results)}")
                
                batch_csv = StringIO()
                if comparison_data:
                    writer = csv.DictWriter(batch_csv, fieldnames=comparison_data[0].keys())
                    writer.writeheader()
                    writer.writerows(comparison_data)
                
                st.download_button(
                    label="📥 Download Batch Results CSV",
                    data=batch_csv.getvalue(),
                    file_name=f"batch_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='font-size: 0.9em;'>This tool provides a preliminary compliance assessment. For legal compliance verification, consult with a privacy attorney.</p>
        <p style='font-size: 1.1em; margin-top: 15px;'>Made with love ❤️ by Sribalaji</p>
    </div>
    """,
    unsafe_allow_html=True
)
