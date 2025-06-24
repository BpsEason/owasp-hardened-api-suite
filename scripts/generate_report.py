import xml.etree.ElementTree as ET
import json
import sys
import os
import logging
from datetime import datetime

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_junit_xml(file_path):
    """解析 JUnit XML 報告."""
    if not os.path.exists(file_path):
        logger.warning(f"JUnit XML 報告未找到: {file_path}")
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        test_suites = root.findall('testsuite') or root.findall('testsuites')
        
        total_tests = 0
        total_failures = 0
        test_results = []

        for suite in test_suites:
            total_tests += int(suite.get('tests', 0))
            total_failures += int(suite.get('failures', 0)) + int(suite.get('errors', 0))

            for testcase in suite.findall('testcase'):
                test_name = testcase.get('name')
                class_name = testcase.get('classname')
                failure = testcase.find('failure')
                error = testcase.find('error')

                if failure is not None:
                    test_results.append({
                        'test_name': f"{class_name}.{test_name}",
                        'status': 'FAIL',
                        'type': failure.get('type', ''),
                        'message': failure.get('message', failure.text.strip() if failure.text else ''),
                        'details': (failure.text.strip() if failure.text else '')[:200] + '...' if len(failure.text or '') > 200 else (failure.text.strip() or '')
                    })
                elif error is not None:
                    test_results.append({
                        'test_name': f"{class_name}.{test_name}",
                        'status': 'ERROR',
                        'type': error.get('type', ''),
                        'message': error.get('message', error.text.strip() if error.text else ''),
                        'details': (error.text.strip() if error.text else '')[:200] + '...' if len(error.text or '') > 200 else (error.text.strip() or '')
                    })
                else:
                    test_results.append({
                        'test_name': f"{class_name}.{test_name}",
                        'status': 'PASS',
                        'type': '',
                        'message': 'Test Passed',
                        'details': ''
                    })
        return {
            'total_tests': total_tests,
            'total_failures': total_failures,
            'test_results': test_results
        }
    except Exception as e:
        logger.error(f"解析 JUnit XML 失敗 {file_path}: {e}")
        return None

def parse_zap_json(file_path):
    """解析 ZAP JSON 報告."""
    if not os.path.exists(file_path):
        logger.warning(f"ZAP JSON 報告未找到: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        alerts = []
        for site in report_data.get('site', []):
            for alert_item in site.get('alerts', []):
                alerts.append({
                    'alert_name': alert_item.get('alert', 'Unknown'),
                    'risk_code': alert_item.get('riskcode', '0'),
                    'risk_desc': alert_item.get('riskdesc', 'Unknown'),
                    'confidence': alert_item.get('confidence', 'Unknown'),
                    'instances_count': len(alert_item.get('instances', []))
                })
        return alerts
    except Exception as e:
        logger.error(f"解析 ZAP JSON 失敗 {file_path}: {e}")
        return None

def generate_markdown_report(pytest_report_data, phpunit_report_data, zap_alerts):
    """生成 Markdown 報告."""
    report_content = [f"## OWASP Hardened API Suite Security Report\n\n"]
    report_content.append(f"**Generated Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report_content.append("---\n\n")

    # --- Pytest 報告 ---
    report_content.append("### 🧪 FastAPI Pytest Security Results\n\n")
    if pytest_report_data:
        report_content.append(f"- Total Tests: **{pytest_report_data['total_tests']}**\n")
        report_content.append(f"- Failed Tests: **{pytest_report_data['total_failures']}**\n\n")
        
        report_content.append("| Test Name | Status | Message |\n")
        report_content.append("| :------- | :----- | ------ |\n")
        for test in pytest_report_data['test_results']:
            status_emoji = "✅" if test['status'] == "PASS" else "❌"
            report_content.append(f"| `{test['test_name']}` | {status_emoji} {test['status']} | {test['message']} |\n")
        report_content.append("\n")
    else:
        report_content.append("No valid FastAPI Pytest report found or parsing failed.\n\n")

    # --- PHPUnit 報告 ---
    report_content.append("### 🐘 Laravel PHPUnit Security Results\n\n")
    if phpunit_report_data:
        report_content.append(f"- Total Tests: **{phpunit_report_data['total_tests']}**\n")
        report.append(f"- Failed Tests: **{phpunit_report_data['total_failures']}**\n\n")
        
        report_content.append("| Test Name | Status | Message |\n")
        report_content.append("| :------- | :----- | ------ |\n")
        for test in phpunit_report_data['test_results']:
            status_emoji = "✅" if test['status'] == "PASS" else "❌"
            report_content.append(f"| `{test['test_name']}` | {status_emoji} {test['status']} | {test['message']} |\n")
        report_content.append("\n")
    else:
        report_content.append("No valid Laravel PHPUnit report found or parsing failed.\n\n")

    # --- ZAP 報告 ---
    report_content.append("### 🛡️ ZAP Dynamic Analysis Results\n\n")
    if zap_alerts is not None:
        if zap_alerts:
            report_content.append("| Alert Name | Risk Level | Confidence | Instances |\n")
            report_content.append("| :--------- | :--------- | :--------- | :-------- |\n")
            for alert in zap_alerts:
                risk_emoji = "🔴" if alert['risk_code'] == '3' else ("🟠" if alert['risk_code'] == '2' else ("🟡" if alert['risk_code'] == '1' else "⚪"))
                report_content.append(f"| {alert['alert_name']} | {risk_emoji} {alert['risk_desc']} | {alert['confidence']} | {alert['instances_count']} |\n")
            report_content.append("\nFull ZAP JSON report available in CI/CD artifacts.\n\n")
        else:
            report_content.append("ZAP scan completed. No high-severity alerts found.\n\n")
    else:
        report_content.append("No valid ZAP JSON report found or parsing failed.\n\n")

    return ''.join(report_content)

if __name__ == "__main__":
    pytest_report_path = os.getenv('PYTEST_REPORT_PATH', 'pytest-report.xml')
    phpunit_report_path = os.getenv('PHPUNIT_REPORT_PATH', 'laravel-report.xml')
    zap_report_path = os.getenv('ZAP_REPORT_PATH', 'zap-reports/zap_report.json')
    output_markdown_path = os.getenv('OUTPUT_MARKDOWN_PATH', 'reports/summary.md') # 統一路徑為 reports/summary.md

    logger.info(f"Processing reports: pytest={pytest_report_path}, phpunit={phpunit_report_path}, zap={zap_report_path}")

    pytest_data = parse_junit_xml(pytest_report_path)
    phpunit_data = parse_junit_xml(phpunit_report_path)
    zap_data = parse_zap_json(zap_report_path)

    markdown_output = generate_markdown_report(pytest_data, phpunit_data, zap_data)

    output_dir = os.path.dirname(output_markdown_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        logger.info(f"安全報告已成功生成至: {output_markdown_path}")
    except IOError as e:
        logger.error(f"寫入報告檔案失敗 {output_markdown_path}: {e}")
        sys.exit(1)

    # Exit with a non-zero code if there are any failures or significant alerts
    if (pytest_data and pytest_data['total_failures'] > 0) or \
       (phpunit_data and phpunit_data['total_failures'] > 0) or \
       (zap_data and any(alert['risk_code'] in ['3', '2'] for alert in zap_data)): # Consider high (3) and medium (2) risks as failures
        logger.error("偵測到安全測試失敗或高/中風險警報。")
        sys.exit(1)
    else:
        logger.info("所有安全測試通過，且未偵測到高/中風險警報。")
