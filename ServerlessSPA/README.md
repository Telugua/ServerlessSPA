# AWS CloudFormation S3web+Pipeline and CloudFrontTemplate

This project documents and delivers a reproducible pattern to establish a 'static website' (e.g. Javascript Single Page Application) hosted via S3 accessible only within PG&E UDN, and delivered / secured using the following collection of AWS Services:
* CloudFront Content Distribution Network
* AWS Web Application Firewall (WAF)
* AWS Certificate Manager
* AWS Route 53 (DNS)

Note: For PG&E, S3 hosted websites must currently only be available via intranet and not publicly available.  This is achieved using AWS WAF and associated rules.

This product is a collection of multiple CloudFormation templates, orchestrated and executed through Step Functions and Lambda.

* [Design Pattern Diagram](/images/aws-cfn-s3web.png)

For setting up the S3 Pipeline, choose the appropriate pattern for your case:

* Angular-based (S3web+Pipeline+Angular)
* React-based (S3web+Pipeline+React)
* HTML-based (S3web+Pipeline+HTML)

For setting up the CloudFront distribution, there is only one template that applies to either of the Pipeline patterns.


This pattern is also documented in [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670).  Wiki may contain additional information as well as tips.

## Getting Started

These instructions will enable you to launch this pattern in an PG&E Amazon Web Services (AWS) environment. See Prerequisites and deployment for notes on how to deploy the project into a target AWS environment.  For easy access to the CloudFormation templates, you can clone this project to your local machine with (this assumes access to DigitalCatalyst GitHub organization):

```
$ git clone https://github.com/pgetech/aws-cfn-s3web.git
```
This pattern is designed for use in any Cloud COE provided AWS accounts.

## Scenarios

* S3web+Pipeline+Angular - AWS S3 hosted Single Page Application written in Angular
* S3web+Pipeline+HTML - AWS S3 hosted website using HTML (the pipeline will copy files from the html folder in your corresponding GitHub branch (dev, prod, QA, etc.) in repo. Take note that you **must setup a folder named "html" within the given branch you choose**. And this is where your html files must reside.
* S3web+Pipeline+React - AWS S3 hosted website using React framework.

## Prerequisites

This design pattern requires:
* An active AWS account
* A Federated or IAM User with permissions to CloudFormation and provisioned resources
* A GitHub repository (with at least one branch).
* Certificate, Domain Registration and DNS setup which will resolve your Fully Qualified Domain Names (FQDNs) -- Route53, PowerDNS, InfoBlox, BIND, etc.
  * A certificate is required for the S3 Webhost name (FQDN)
  * Domain Registration may be needed if not already registered
  * DNS Entry for CloudDistribution
  * See [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670) for process
* Web Application Rules have been created that limit to PG&E UDN ip ranges  - refer to
[Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670) for more information on this topic.

## Installing

This project consists of three primary CloudFormation templates:
* *aws-cfn-s3web-pipeline-angular.yaml*:  Creates S3 bucket for web hosting, S3 bucket for build artifacts,integrates to Github repository, and creates CodePipeline and CodeBuild services that build an Angular Webapp using ng build.

* *aws-cfn-s3web-pipeline-html.yaml*: Creates S3 bucket for web hosting, S3 bucket for build artifacts,integrates to Github repository, and CodePipeline and CodeBuild services that copy the html or dist folder from the Github repo to the S3 hosting bucket.

* *aws-cfn-cloudfront.yaml*: CloudFront template creates CloudFront distribution, configures the distribution to utilize WAF Web ACL's for PG&E IP range, and sets logging for the CloudFront distribution to a centralized logging bucket. The WAF rules limit the S3 Webhost bucket to PG&E UDN.

### Setting Up Your Pipeline
 Follow the steps below to create a CloudFormation stack. You will use one of these three YAML files depending upon your S3 Web type:
 
  * *aws-cfn-s3web-pipeline-angular.yaml*
  * *aws-cfn-s3web-pipeline-html.yaml*
  * *aws-cfn-s3web-pipeline-dc-react.yaml*
  
 **CloudFormation steps:**
 
  1. Login to AWS console, and open the desiredAWS region.  (note that your S3 buckets will created in the region chosen)
  
  2. Open CloudFormation
  
  3. When CloudFormation starts, click on Create Stack
  
  4. Click Design Template
  
  5. On the Parameters window, select Template tab (default is Compoments)
  
  6. Choose YAML as the Template language
  
  7. Overwrite the existing code snippet in the code window and paste the YAML code in it's place
  
  8. Click on Create Stack icon (looks like a cloud) near the top of the page
      *this brings you back to the Select Template window - you should see that "Specify and Amazon S3 template URL" is now populated with information.

  9. Click next
  
  10. You will need to fill in the following parameters on the subsequent page:
  
      * **Stack name** : Name for your stack
    
      * **pApplicationName** : Name of this application
    
      * **pCFNOwnerTag** : The owner of this stack for tagging of resources.  Typically LANID of the owner of this application
    
      * **pEnv** : Environment of this stack (Dev, QA, Production)
      
      * **pGitHubAccount** : The GitHub Account Name (e.g. PGEDigitalCatalyst)
       
      * **pGitHubRepo** : Name of your GitHub repository (no prefix or FQDN)
       
      * **pGitHubRepoBranch** : Branch for your repo. Default is master
      
      * **pGitHubToken** :  Once deployed, Don't change this value** : First time, create a new Github Personal OAuth token. Be sure to store ths in AWS Secrets Manager for future use.
    
      * **pPipelineBucketName** : The name of the bucket that will contain the pipeline artifacts
    
      * **pProjectBucketName** : Name for the bucket that will contain the built project (must be in FQDN format - eg. engage-dev.digitalcatalyst.pge.com)
      
      * **pReferer** : The referer header value for restricting access to S3. This value is a random key that you choose.  Suggest a 64 character string utilizing numbers, letters, special characters etc. Once created, store this in AWS Secrets. This key will be used below in the CloudFormation template below.
      
  11. Click next
  
  12. On this page, add Tags.  At a miminum, **App Name**, **Owner**, and **Env**.  All other fieids can be left as is.
  
  13. Click next - this screen be be left as default
  
  14. Click create

  15. For the pipeline cloudformation templates, once you click on create in step 12, you will need to click on the checkbox - "I acknowledge might create IAM resources with custom names". This checkbox does not apply to the cloudformation template as described below.
  
  > NOTE: Once the CloudFormation template completes, the pipeline will automatically kick off and pull your code from GitHub, and deploy it to S3.

### Setting Up Your CloudFront Distribution
 > Note: Prior to creating this CloudFront Distribution CloudFormation stack, the domain must be registered, cname and AWS certificate must be setup .  If you are unfamiliar with this process, refer to the [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670) for updated information.
 
 **CloudFormation steps**
Once the pipeline cloud front scripts are complete, start a new CloudFormation stack using
the template:  **aws-cfn-cloudfront.yaml**.

Refer to "setting up your pipeline above and **complete steps 1-9**.

 You will need to fill in the following parameters on the subsequent page:

  * **Stack Name** : Name of the stack
    
  * **pApplicationName** : The name of the application - typically the same Application name created for the pipeline templates in the "Setting up the pipeline section above"
  
  * **pCFCertificateArn** : obtain this from AWS Certificate Manager - see note above and refer to [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670) for updated information
    
  * **pCFNOwnerTag** : The owner of this stack (for tagging of resources)
    
  * **pEnv** : Environment of this stack (Dev, QA, Production)
    
  * **pFrontendS3BucketDomain** : must match pProjectBucketName parameter above (eg. engage-dev.digitalcatalyst.pge.com)
    
  * **pHostedZoneName** : (eg. digitalcatalyst.pge.com)
  
  * **pRefererValue** : The referer header value for restricting access to S3. This value is a random key that you choose.  Suggest a 64 character string utilizing numbers, letters, special characters etc. Once created, store this in AWS Secrets. Use the same key that you generated above for the S3 Pipeline setup.
    
  * **pSiteName:** : (eg. engage-dev)
    
  * **pWebACLId** : AWS WAF Web ACL **ID** - to limit ipaddress range to PG&E etc. This WAF rule should alredady be setup in AWS. If not, consult the [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670) for further information.  *(example: 472a8774-985a-49e2-ab40-cfdd4173ab3e)*
  
  Once you have completed these steps, refer to "setting up your pipeline" above and **complete steps 11-15**.

  After Cloudfront is complete, PG&E DNS must be setup.  Refer to [Wiki](https://wiki.comp.pge.com/pages/viewpage.action?pageId=49952670). You will need to obtain the CloudFront Distribution Name in order to complete the DNS change.

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## TODO
* Orchestrate Multiple Templates with Step Functions for One-Click Deploy : CLOUDCOE-2653
* Integrate Product into Service Catalog : CLOUDCOE-2657
* Abstract the Buildspec file(s) so the Cloud Formation template reads them from the Repo
* Find a way to have one pipeline with multiple S3 bucket destinations based on the Branch




