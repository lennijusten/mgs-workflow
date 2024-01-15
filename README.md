# Nextflow MGS Analysis

Runs metagenomic sequencing data through a pipeline that includes adapter removal, deduplication, host DNA and ribosomal RNA depletion, and taxonomic assignment.

## Dependencies

### Nextflow

You need to install Java 17 for Nextflow to run (we use Amazon Corretto 17):

```
sudo yum install java-17-amazon-corretto-headless \
wget -qO- https://get.nextflow.io | bash \
chmod +x nextflow
```




