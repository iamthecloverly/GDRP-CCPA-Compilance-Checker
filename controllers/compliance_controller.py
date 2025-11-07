from models.compliance_model import ComplianceModel
from services.openai_service import analyze_privacy_policy, get_compliance_recommendations
from typing import Dict


class ComplianceController:
    def __init__(self, url: str):
        self.url = url
        self.model = ComplianceModel(url)
        self.results = {}
    
    def run_scan(self, include_ai_analysis: bool = True) -> Dict:
        self.results = self.model.run_all()
        
        if 'error' in self.results:
            return self.results
        
        if include_ai_analysis:
            privacy_policy = self.results.get('privacy_policy', {})
            
            if privacy_policy.get('found') and privacy_policy.get('links'):
                policy_url = privacy_policy['links'][0]['url']
                
                ai_analysis = analyze_privacy_policy(policy_url)
                self.results['policy_analysis'] = ai_analysis
            else:
                self.results['policy_analysis'] = {
                    'error': 'No privacy policy found to analyze',
                    'gdpr_compliant': False,
                    'ccpa_compliant': False
                }
            
            recommendations = get_compliance_recommendations(self.results)
            self.results['recommendations'] = recommendations
        
        self.results['compliance_summary'] = self._calculate_compliance_summary()
        
        return self.results
    
    def _calculate_compliance_summary(self) -> Dict:
        checks_passed = 0
        total_checks = 4
        
        if self.results.get('cookie_banner', {}).get('detected'):
            checks_passed += 1
        
        if self.results.get('privacy_policy', {}).get('found'):
            checks_passed += 1
        
        if self.results.get('contact_info', {}).get('detected'):
            checks_passed += 1
        
        policy_analysis = self.results.get('policy_analysis', {})
        if not policy_analysis.get('error'):
            if policy_analysis.get('gdpr_compliant') or policy_analysis.get('ccpa_compliant'):
                checks_passed += 1
        
        compliance_percentage = (checks_passed / total_checks) * 100
        
        if compliance_percentage >= 75:
            status = 'Good'
            color = 'green'
        elif compliance_percentage >= 50:
            status = 'Fair'
            color = 'orange'
        else:
            status = 'Needs Improvement'
            color = 'red'
        
        return {
            'checks_passed': checks_passed,
            'total_checks': total_checks,
            'compliance_percentage': compliance_percentage,
            'status': status,
            'color': color
        }
