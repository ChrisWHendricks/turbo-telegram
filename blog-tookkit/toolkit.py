#!/usr/bin/env python3
"""
AWS Blog Infrastructure Setup Toolkit
=====================================

This toolkit provides scripts to automatically set up a secure, cost-effective
blog infrastructure on AWS using S3, CloudFront, Route53, and ACM.

Requirements:
- boto3: pip install boto3
- AWS CLI configured with appropriate permissions
- Domain already registered in Route53
"""

import boto3
import json
import time
import sys
from typing import Dict, Optional, List
from botocore.exceptions import ClientError


class BlogInfrastructure:
    """Main class for managing blog infrastructure setup"""
    
    def __init__(self, domain_name: str, aws_profile: Optional[str] = None):
        self.domain_name = domain_name
        self.www_domain = f"www.{domain_name}"
        self.bucket_name = domain_name
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self.s3 = session.client('s3')
        self.cloudfront = session.client('cloudfront')
        self.route53 = session.client('route53')
        self.acm = session.client('acm', region_name='us-east-1')  # ACM must be in us-east-1 for CloudFront
        
        # Store resource IDs for reference
        self.resources = {
            'bucket_name': self.bucket_name,
            'certificate_arn': None,
            'distribution_id': None,
            'hosted_zone_id': None
        }
    
    def create_s3_bucket(self) -> bool:
        """Create S3 bucket for static website hosting"""
        try:
            print(f"Creating S3 bucket: {self.bucket_name}")
            
            # Create bucket
            if self.s3.meta.region_name == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.s3.meta.region_name}
                )
            
            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Block public access (security best practice)
            self.s3.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            print(f"✓ S3 bucket {self.bucket_name} created successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"✓ S3 bucket {self.bucket_name} already exists")
                return True
            else:
                print(f"✗ Error creating S3 bucket: {e}")
                return False
    
    def request_ssl_certificate(self) -> Optional[str]:
        """Request SSL certificate from ACM"""
        try:
            print("Requesting SSL certificate from ACM...")
            
            response = self.acm.request_certificate(
                DomainName=self.domain_name,
                SubjectAlternativeNames=[self.www_domain],
                ValidationMethod='DNS',
                Tags=[
                    {'Key': 'Name', 'Value': f'{self.domain_name} Blog Certificate'},
                    {'Key': 'Purpose', 'Value': 'Blog'}
                ]
            )
            
            certificate_arn = response['CertificateArn']
            self.resources['certificate_arn'] = certificate_arn
            
            print(f"✓ SSL certificate requested: {certificate_arn}")
            print("⚠ You need to validate the certificate via DNS records in Route53")
            print("  Use the AWS Console or get_certificate_validation_records() method")
            
            return certificate_arn
            
        except ClientError as e:
            print(f"✗ Error requesting SSL certificate: {e}")
            return None
    
    def get_certificate_validation_records(self, certificate_arn: str) -> List[Dict]:
        """Get DNS validation records for certificate"""
        try:
            response = self.acm.describe_certificate(CertificateArn=certificate_arn)
            validation_options = response['Certificate']['DomainValidationOptions']
            
            records = []
            for option in validation_options:
                if 'ResourceRecord' in option:
                    records.append({
                        'domain': option['DomainName'],
                        'name': option['ResourceRecord']['Name'],
                        'value': option['ResourceRecord']['Value'],
                        'type': option['ResourceRecord']['Type']
                    })
            
            return records
            
        except ClientError as e:
            print(f"✗ Error getting certificate validation records: {e}")
            return []
    
    def get_hosted_zone_id(self) -> Optional[str]:
        """Get Route53 hosted zone ID for the domain"""
        try:
            response = self.route53.list_hosted_zones()
            
            for zone in response['HostedZones']:
                if zone['Name'].rstrip('.') == self.domain_name:
                    self.resources['hosted_zone_id'] = zone['Id']
                    return zone['Id']
            
            print(f"✗ Hosted zone for {self.domain_name} not found")
            return None
            
        except ClientError as e:
            print(f"✗ Error finding hosted zone: {e}")
            return None
    
    def create_cloudfront_distribution(self, certificate_arn: str) -> Optional[str]:
        """Create CloudFront distribution"""
        try:
            print("Creating CloudFront distribution...")
            
            # Origin Access Control configuration
            oac_response = self.cloudfront.create_origin_access_control(
                OriginAccessControlConfig={
                    'Name': f'{self.domain_name}-oac',
                    'Description': f'OAC for {self.domain_name} blog',
                    'SigningProtocol': 'sigv4',
                    'SigningBehavior': 'always',
                    'OriginAccessControlOriginType': 's3'
                }
            )
            
            oac_id = oac_response['OriginAccessControl']['Id']
            
            # CloudFront distribution configuration
            distribution_config = {
                'CallerReference': f'{self.domain_name}-{int(time.time())}',
                'Comment': f'Blog distribution for {self.domain_name}',
                'DefaultRootObject': 'index.html',
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': f'{self.bucket_name}-origin',
                            'DomainName': f'{self.bucket_name}.s3.amazonaws.com',
                            'S3OriginConfig': {
                                'OriginAccessIdentity': ''
                            },
                            'OriginAccessControlId': oac_id
                        }
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': f'{self.bucket_name}-origin',
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'MinTTL': 0,
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    }
                },
                'Enabled': True,
                'Aliases': {
                    'Quantity': 2,
                    'Items': [self.domain_name, self.www_domain]
                },
                'ViewerCertificate': {
                    'ACMCertificateArn': certificate_arn,
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.2_2021'
                },
                'PriceClass': 'PriceClass_100'  # Use only North America and Europe for cost savings
            }
            
            response = self.cloudfront.create_distribution(
                DistributionConfig=distribution_config
            )
            
            distribution_id = response['Distribution']['Id']
            domain_name = response['Distribution']['DomainName']
            
            self.resources['distribution_id'] = distribution_id
            self.resources['cloudfront_domain'] = domain_name
            
            print(f"✓ CloudFront distribution created: {distribution_id}")
            print(f"  Domain: {domain_name}")
            print("⚠ Distribution deployment takes 15-20 minutes")
            
            # Generate S3 bucket policy for OAC
            self._update_s3_bucket_policy(distribution_id)
            
            return distribution_id
            
        except ClientError as e:
            print(f"✗ Error creating CloudFront distribution: {e}")
            return None
    
    def _update_s3_bucket_policy(self, distribution_id: str):
        """Update S3 bucket policy to allow CloudFront access"""
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudfront.amazonaws.com"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": f"arn:aws:cloudfront::{boto3.client('sts').get_caller_identity()['Account']}:distribution/{distribution_id}"
                        }
                    }
                }
            ]
        }
        
        try:
            self.s3.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✓ S3 bucket policy updated for CloudFront access")
            
        except ClientError as e:
            print(f"✗ Error updating S3 bucket policy: {e}")
    
    def create_route53_records(self, cloudfront_domain: str) -> bool:
        """Create Route53 A records pointing to CloudFront"""
        hosted_zone_id = self.get_hosted_zone_id()
        if not hosted_zone_id:
            return False
        
        try:
            print("Creating Route53 DNS records...")
            
            # Create A record for root domain
            self.route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': self.domain_name,
                                'Type': 'A',
                                'AliasTarget': {
                                    'DNSName': cloudfront_domain,
                                    'EvaluateTargetHealth': False,
                                    'HostedZoneId': 'Z2FDTNDATAQYW2'  # CloudFront hosted zone ID
                                }
                            }
                        }
                    ]
                }
            )
            
            # Create A record for www subdomain
            self.route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': self.www_domain,
                                'Type': 'A',
                                'AliasTarget': {
                                    'DNSName': cloudfront_domain,
                                    'EvaluateTargetHealth': False,
                                    'HostedZoneId': 'Z2FDTNDATAQYW2'
                                }
                            }
                        }
                    ]
                }
            )
            
            print(f"✓ Route53 records created for {self.domain_name} and {self.www_domain}")
            return True
            
        except ClientError as e:
            print(f"✗ Error creating Route53 records: {e}")
            return False
    
    def upload_sample_content(self):
        """Upload a sample index.html file"""
        sample_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {self.domain_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .content {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to {self.domain_name}</h1>
        <p>Your secure AWS blog is now live!</p>
    </div>
    <div class="content">
        <h2>Setup Complete</h2>
        <p>Your blog infrastructure has been successfully deployed with:</p>
        <ul>
            <li>✓ S3 bucket for static content storage</li>
            <li>✓ CloudFront CDN for fast, secure delivery</li>
            <li>✓ SSL certificate for HTTPS</li>
            <li>✓ Route53 DNS configuration</li>
        </ul>
        <p>You can now upload your blog content to replace this page.</p>
    </div>
</body>
</html>"""
        
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key='index.html',
                Body=sample_html,
                ContentType='text/html'
            )
            print("✓ Sample index.html uploaded")
            
        except ClientError as e:
            print(f"✗ Error uploading sample content: {e}")
    
    def deploy_full_infrastructure(self) -> Dict:
        """Deploy the complete blog infrastructure"""
        print(f"🚀 Starting deployment for {self.domain_name}")
        print("=" * 50)
        
        # Step 1: Create S3 bucket
        if not self.create_s3_bucket():
            return {'success': False, 'step': 'S3 bucket creation'}
        
        # Step 2: Request SSL certificate
        certificate_arn = self.request_ssl_certificate()
        if not certificate_arn:
            return {'success': False, 'step': 'SSL certificate request'}
        
        # Step 3: Wait for certificate validation (manual step)
        print("\n⚠ MANUAL STEP REQUIRED:")
        print("1. Go to AWS Certificate Manager console")
        print("2. Find your certificate and validate it via DNS")
        print("3. Wait for certificate status to become 'Issued'")
        print("4. Then run create_cloudfront_distribution() method")
        
        return {
            'success': True,
            'step': 'Certificate validation required',
            'certificate_arn': certificate_arn,
            'next_steps': [
                'Validate SSL certificate in ACM console',
                'Run create_cloudfront_distribution() when certificate is issued',
                'Run create_route53_records() after CloudFront is deployed'
            ]
        }
    
    def get_status(self) -> Dict:
        """Get current status of all resources"""
        status = {
            'domain': self.domain_name,
            'resources': self.resources.copy()
        }
        
        # Check S3 bucket
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            status['s3_bucket'] = 'exists'
        except ClientError:
            status['s3_bucket'] = 'missing'
        
        # Check certificate
        if self.resources['certificate_arn']:
            try:
                response = self.acm.describe_certificate(
                    CertificateArn=self.resources['certificate_arn']
                )
                status['certificate_status'] = response['Certificate']['Status']
            except ClientError:
                status['certificate_status'] = 'error'
        
        # Check CloudFront distribution
        if self.resources['distribution_id']:
            try:
                response = self.cloudfront.get_distribution(
                    Id=self.resources['distribution_id']
                )
                status['distribution_status'] = response['Distribution']['Status']
            except ClientError:
                status['distribution_status'] = 'error'
        
        return status


def main():
    """CLI interface for the blog infrastructure toolkit"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Blog Infrastructure Setup')
    parser.add_argument('domain', help='Your domain name (e.g., example.com)')
    parser.add_argument('--profile', help='AWS profile to use')
    parser.add_argument('--action', choices=['deploy', 'status', 'upload-sample'], 
                       default='deploy', help='Action to perform')
    
    args = parser.parse_args()
    
    # Initialize the infrastructure manager
    blog = BlogInfrastructure(args.domain, args.profile)
    
    if args.action == 'deploy':
        result = blog.deploy_full_infrastructure()
        print(f"\nDeployment result: {result}")
        
    elif args.action == 'status':
        status = blog.get_status()
        print(f"\nInfrastructure status:")
        print(json.dumps(status, indent=2))
        
    elif args.action == 'upload-sample':
        blog.upload_sample_content()


if __name__ == '__main__':
    main()