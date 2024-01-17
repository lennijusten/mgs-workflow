# Nextflow MGS Analysis on EC2

Runs metagenomic sequencing data through a pipeline that includes adapter removal, deduplication, host DNA and ribosomal RNA depletion, and taxonomic assignment.

## Dependencies

### Nextflow

You need to install Java 17 for Nextflow to run (we use Amazon Corretto 17):

```
sudo yum install java-17-amazon-corretto-headless \
wget -qO- https://get.nextflow.io | bash \
chmod +x nextflow
```

### AWS S3

#### AWS S3 Access

Our Nextflow pipeline seamlessly works with AWS S3. In order for this to work properly you need to set up your AWS credentials using `aws configure`. If you do not yet have credentials you can ask a senior team member to receive them.

Furthermore, Nextflow won't be able to access S3 buckets that have access controls. To provide Nextflow with your AWS credentials, you can provide them via environment variables like so:
```
export AWS_ACCESS_KEY_ID=<your_access_key_id>
export AWS_SECRET_ACCESS_KEY=<your_secret_access_key>
```
**TODO: Is this a permanent fix? Check in with Jeff about something more permanent**.

#### AWS Bucket

In order to not interfere with other people's work you should create your own S3 bucket ([instructions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)). To direct Nextflow toward your new bucket, change the `s3_dir` variable in your `configs/*.config` files accordingly.

### Docker

The computational tools used in the pipeline run in Docker containers.
```
sudo yum install docker \
sudo service docker start \
sudo usermod -a -G docker ec2-user
```
Sometimes you need to restart your EC2 instance to get Docker to run properly after setup.:wq
:

## Running Nextflow

The pipeline steps that handle sequencing files are contained within `workflows/main.nf`:. Before running this script we need to create the indices used by various tools such as BBTools, Kraken, or Bowtie2. 


