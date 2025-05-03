"""
Technology detector for passive scanning
"""
import logging
import re
import json
from bs4 import BeautifulSoup
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def detect_technologies(response_text, response_headers):
    """
    Detect technologies used by a website based on headers and HTML content
    
    Args:
        response_text (str): HTML content
        response_headers (dict): HTTP response headers
        
    Returns:
        dict: Detected technologies
    """
    technologies = {
        'server': response_headers.get('Server', 'Unknown'),
        'frameworks': [],
        'cms': None,
        'javascript_libraries': [],
        'programming_languages': [],
        'web_servers': [],
        'analytics': [],
        'cdn': None
    }
    
    # Ensure response_text is a string
    if response_text is None:
        response_text = ""
    
    if not isinstance(response_text, str):
        response_text = str(response_text)
    
    # Create BeautifulSoup object for better HTML parsing
    soup = BeautifulSoup(response_text, 'html.parser')
    
    # Detect CMS
    detect_cms(soup, response_text, response_headers, technologies)
    
    # Detect frameworks
    detect_frameworks(soup, response_text, response_headers, technologies)
    
    # Detect JavaScript libraries
    detect_js_libraries(soup, response_text, technologies)
    
    # Detect programming languages
    detect_programming_languages(response_headers, technologies)
    
    # Detect web servers
    detect_web_servers(response_headers, technologies)
    
    # Detect analytics
    detect_analytics(soup, response_text, technologies)
    
    # Detect CDN
    detect_cdn(response_headers, technologies)
    
    # Remove duplicates
    technologies['frameworks'] = list(set(technologies['frameworks']))
    technologies['javascript_libraries'] = list(set(technologies['javascript_libraries']))
    technologies['programming_languages'] = list(set(technologies['programming_languages']))
    technologies['web_servers'] = list(set(technologies['web_servers']))
    technologies['analytics'] = list(set(technologies['analytics']))
    
    return technologies

def detect_cms(soup, response_text, response_headers, technologies):
    """
    Detect Content Management Systems
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        response_text (str): Raw HTML content
        response_headers (dict): HTTP response headers
        technologies (dict): Technology dictionary to update
    """
    # WordPress detection
    if any(term in response_text.lower() for term in ['wp-content', 'wp-includes', 'wordpress']):
        technologies['cms'] = 'WordPress'
        
        # Look for version
        wp_version_meta = soup.find('meta', {'name': 'generator'})
        if wp_version_meta and 'content' in wp_version_meta.attrs:
            content = wp_version_meta['content']
            if 'wordpress' in content.lower():
                technologies['cms'] = f"WordPress {content.split(' ')[1]}"
    
    # Drupal detection
    elif any(term in response_text.lower() for term in ['drupal.settings', 'drupal.org', '/sites/all/themes/']):
        technologies['cms'] = 'Drupal'
        
        # Check for Drupal version in generator tag
        drupal_meta = soup.find('meta', {'name': 'generator'})
        if drupal_meta and 'content' in drupal_meta.attrs:
            content = drupal_meta['content']
            if 'drupal' in content.lower():
                technologies['cms'] = f"Drupal {content.split(' ')[1]}"
    
    # Joomla detection
    elif any(term in response_text.lower() for term in ['joomla!', '/components/com_', '/media/jui/']):
        technologies['cms'] = 'Joomla'
        
        # Look for version in meta
        joomla_meta = soup.find('meta', {'name': 'generator'})
        if joomla_meta and 'content' in joomla_meta.attrs:
            content = joomla_meta['content']
            if 'joomla' in content.lower():
                technologies['cms'] = f"Joomla {content.split(' ')[1]}"
    
    # Magento detection
    elif any(term in response_text.lower() for term in ['magento', 'mage/cookies.js', 'enterprise_cms']):
        technologies['cms'] = 'Magento'
    
    # Shopify detection
    elif any(term in response_text.lower() for term in ['shopify.com', '/cdn.shopify.com/']):
        technologies['cms'] = 'Shopify'
    
    # Wix detection
    elif any(term in response_text.lower() for term in ['wix.com', '_wixCssrules', '_wixads']):
        technologies['cms'] = 'Wix'
    
    # Squarespace detection
    elif any(term in response_text.lower() for term in ['squarespace.com', 'static.squarespace.com']):
        technologies['cms'] = 'Squarespace'
    
    # Ghost detection
    elif 'content="Ghost' in response_text:
        technologies['cms'] = 'Ghost'
        
        # Look for version
        ghost_meta = soup.find('meta', {'name': 'generator'})
        if ghost_meta and 'content' in ghost_meta.attrs:
            content = ghost_meta['content']
            if 'ghost' in content.lower():
                technologies['cms'] = content

def detect_frameworks(soup, response_text, response_headers, technologies):
    """
    Detect web frameworks
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        response_text (str): Raw HTML content
        response_headers (dict): HTTP response headers
        technologies (dict): Technology dictionary to update
    """
    # Django detection
    if 'csrfmiddlewaretoken' in response_text or '__admin_media_prefix__' in response_text:
        technologies['frameworks'].append('Django')
    
    # Flask detection
    if 'flask' in response_headers.get('Server', '').lower():
        technologies['frameworks'].append('Flask')
    
    # Ruby on Rails detection
    if 'rails' in response_text.lower() or '_rails_env' in response_text:
        technologies['frameworks'].append('Ruby on Rails')
    elif 'data-turbolinks-track' in response_text:
        technologies['frameworks'].append('Ruby on Rails')
    elif 'x-powered-by' in response_headers and 'rails' in response_headers.get('x-powered-by', '').lower():
        technologies['frameworks'].append('Ruby on Rails')
    
    # Express.js detection
    if 'express' in response_headers.get('x-powered-by', '').lower():
        technologies['frameworks'].append('Express.js')
    
    # Laravel detection
    if 'laravel' in response_text.lower() or 'laravel_session' in response_text:
        technologies['frameworks'].append('Laravel')
    elif 'laravel-token' in response_text:
        technologies['frameworks'].append('Laravel')
    
    # ASP.NET detection
    if 'asp.net' in response_text.lower() or '__VIEWSTATE' in response_text:
        technologies['frameworks'].append('ASP.NET')
    elif 'asp.net' in response_headers.get('x-powered-by', '').lower():
        technologies['frameworks'].append('ASP.NET')
    elif 'x-aspnet-version' in response_headers:
        technologies['frameworks'].append(f"ASP.NET {response_headers['x-aspnet-version']}")
    
    # Spring Framework detection
    if 'org.springframework' in response_text:
        technologies['frameworks'].append('Spring')
    
    # Angular detection
    if 'ng-app' in response_text or 'ng-controller' in response_text:
        technologies['frameworks'].append('Angular')
    elif 'angular.js' in response_text or 'angular.min.js' in response_text:
        technologies['frameworks'].append('Angular')
    
    # React detection
    if 'react.js' in response_text or 'react.min.js' in response_text:
        technologies['frameworks'].append('React')
    elif 'react-dom' in response_text:
        technologies['frameworks'].append('React')
    elif '_reactRootContainer' in response_text:
        technologies['frameworks'].append('React')
    
    # Vue.js detection
    if 'vue.js' in response_text or 'vue.min.js' in response_text:
        technologies['frameworks'].append('Vue.js')
    elif 'data-v-' in response_text:
        technologies['frameworks'].append('Vue.js')

def detect_js_libraries(soup, response_text, technologies):
    """
    Detect JavaScript libraries
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        response_text (str): Raw HTML content
        technologies (dict): Technology dictionary to update
    """
    # Check for script tags with src attribute
    script_tags = soup.find_all('script', src=True)
    for script in script_tags:
        src = script['src'].lower()
        
        # jQuery detection
        if 'jquery' in src:
            technologies['javascript_libraries'].append('jQuery')
            
            # Try to get jQuery version
            match = re.search(r'jquery[.-](\d+\.\d+\.\d+)', src)
            if match:
                technologies['javascript_libraries'][-1] = f"jQuery {match.group(1)}"
        
        # Bootstrap detection
        elif 'bootstrap' in src:
            technologies['javascript_libraries'].append('Bootstrap')
            
            # Try to get Bootstrap version
            match = re.search(r'bootstrap[.-](\d+\.\d+\.\d+)', src)
            if match:
                technologies['javascript_libraries'][-1] = f"Bootstrap {match.group(1)}"
        
        # Moment.js detection
        elif 'moment' in src:
            technologies['javascript_libraries'].append('Moment.js')
        
        # Lodash detection
        elif 'lodash' in src or 'lodash.min.js' in src:
            technologies['javascript_libraries'].append('Lodash')
        
        # D3.js detection
        elif 'd3' in src or 'd3.min.js' in src:
            technologies['javascript_libraries'].append('D3.js')
        
        # Chart.js detection
        elif 'chart.js' in src or 'chart.min.js' in src:
            technologies['javascript_libraries'].append('Chart.js')
        
        # Tailwind CSS detection
        elif 'tailwind' in src:
            technologies['javascript_libraries'].append('Tailwind CSS')
    
    # Look for inline script blocks for evidence of libraries
    for script in soup.find_all('script'):
        if script.string:
            script_content = script.string.lower()
            
            # Check for libraries in inline scripts
            if 'jquery' in script_content and 'jQuery' not in technologies['javascript_libraries']:
                technologies['javascript_libraries'].append('jQuery')
            
            if ('react' in script_content or 'reactdom' in script_content) and 'React' not in technologies['frameworks']:
                technologies['frameworks'].append('React')
            
            if 'vue' in script_content and 'Vue.js' not in technologies['frameworks']:
                technologies['frameworks'].append('Vue.js')
    
    # Check for CSS libraries by looking at link tags
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href', '').lower()
        
        if 'bootstrap' in href and 'Bootstrap' not in technologies['javascript_libraries']:
            technologies['javascript_libraries'].append('Bootstrap')
        
        if 'tailwind' in href and 'Tailwind CSS' not in technologies['javascript_libraries']:
            technologies['javascript_libraries'].append('Tailwind CSS')
        
        if 'fontawesome' in href:
            technologies['javascript_libraries'].append('Font Awesome')

def detect_programming_languages(response_headers, technologies):
    """
    Detect programming languages
    
    Args:
        response_headers (dict): HTTP response headers
        technologies (dict): Technology dictionary to update
    """
    # PHP detection
    if 'php' in response_headers.get('x-powered-by', '').lower():
        technologies['programming_languages'].append('PHP')
        
        # Get PHP version if available
        php_version_match = re.search(r'PHP/(\d+\.\d+\.\d+)', response_headers.get('x-powered-by', ''))
        if php_version_match:
            technologies['programming_languages'][-1] = f"PHP {php_version_match.group(1)}"
    
    # ASP.NET detection
    if 'asp.net' in response_headers.get('x-powered-by', '').lower():
        technologies['programming_languages'].append('.NET')
    
    # Node.js detection
    if 'node.js' in response_headers.get('x-powered-by', '').lower():
        technologies['programming_languages'].append('Node.js')
    
    # Java detection from headers
    if any(java_term in response_headers.get('server', '').lower() for java_term in ['tomcat', 'jetty', 'jboss', 'websphere']):
        technologies['programming_languages'].append('Java')
    
    # Ruby detection
    if 'phusion passenger' in response_headers.get('server', '').lower() or 'ruby' in response_headers.get('x-powered-by', '').lower():
        technologies['programming_languages'].append('Ruby')
    
    # Python detection
    if 'python' in response_headers.get('x-powered-by', '').lower() or 'wsgi' in response_headers.get('server', '').lower():
        technologies['programming_languages'].append('Python')

def detect_web_servers(response_headers, technologies):
    """
    Detect web servers
    
    Args:
        response_headers (dict): HTTP response headers
        technologies (dict): Technology dictionary to update
    """
    server_header = response_headers.get('server', '').lower()
    
    # Apache detection
    if 'apache' in server_header:
        # Extract version if available
        apache_version_match = re.search(r'apache/(\d+\.\d+\.\d+)', server_header)
        if apache_version_match:
            technologies['web_servers'].append(f"Apache {apache_version_match.group(1)}")
        else:
            technologies['web_servers'].append('Apache')
    
    # Nginx detection
    elif 'nginx' in server_header:
        # Extract version if available
        nginx_version_match = re.search(r'nginx/(\d+\.\d+\.\d+)', server_header)
        if nginx_version_match:
            technologies['web_servers'].append(f"Nginx {nginx_version_match.group(1)}")
        else:
            technologies['web_servers'].append('Nginx')
    
    # Microsoft IIS detection
    elif 'microsoft-iis' in server_header:
        # Extract version if available
        iis_version_match = re.search(r'microsoft-iis/(\d+\.\d+)', server_header)
        if iis_version_match:
            technologies['web_servers'].append(f"Microsoft IIS {iis_version_match.group(1)}")
        else:
            technologies['web_servers'].append('Microsoft IIS')
    
    # Tomcat detection
    elif 'tomcat' in server_header:
        technologies['web_servers'].append('Apache Tomcat')
    
    # LiteSpeed detection
    elif 'litespeed' in server_header:
        technologies['web_servers'].append('LiteSpeed')
    
    # Caddy detection
    elif 'caddy' in server_header:
        technologies['web_servers'].append('Caddy')
    
    # Lighttpd detection
    elif 'lighttpd' in server_header:
        technologies['web_servers'].append('Lighttpd')

def detect_analytics(soup, response_text, technologies):
    """
    Detect analytics and tracking scripts
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        response_text (str): Raw HTML content
        technologies (dict): Technology dictionary to update
    """
    # Google Analytics detection
    if 'google-analytics.com' in response_text or 'googletagmanager.com' in response_text:
        technologies['analytics'].append('Google Analytics')
    
    # Google Tag Manager detection
    if 'gtm.js' in response_text or 'gtag' in response_text:
        technologies['analytics'].append('Google Tag Manager')
    
    # Facebook Pixel detection
    if 'connect.facebook.net' in response_text or 'facebook-jssdk' in response_text:
        technologies['analytics'].append('Facebook Pixel')
    
    # Hotjar detection
    if 'hotjar' in response_text:
        technologies['analytics'].append('Hotjar')
    
    # Matomo/Piwik detection
    if 'matomo' in response_text or 'piwik' in response_text:
        technologies['analytics'].append('Matomo/Piwik')
    
    # Adobe Analytics detection
    if 'adobe' in response_text and 'analytics' in response_text:
        technologies['analytics'].append('Adobe Analytics')

def detect_cdn(response_headers, technologies):
    """
    Detect Content Delivery Networks
    
    Args:
        response_headers (dict): HTTP response headers
        technologies (dict): Technology dictionary to update
    """
    # Cloudflare detection
    if 'cf-ray' in response_headers or 'cloudflare' in response_headers.get('server', '').lower():
        technologies['cdn'] = 'Cloudflare'
    
    # Akamai detection
    elif 'akamai' in response_headers.get('server', '').lower():
        technologies['cdn'] = 'Akamai'
    
    # Fastly detection
    elif 'fastly' in response_headers.get('via', '').lower():
        technologies['cdn'] = 'Fastly'
    
    # Cloudfront detection
    elif 'cloudfront' in response_headers.get('via', '').lower() or 'x-amz-cf-id' in response_headers:
        technologies['cdn'] = 'AWS CloudFront'
    
    # Vercel detection
    elif 'x-vercel' in response_headers:
        technologies['cdn'] = 'Vercel'
    
    # Netlify detection
    elif 'x-nf-request-id' in response_headers:
        technologies['cdn'] = 'Netlify'