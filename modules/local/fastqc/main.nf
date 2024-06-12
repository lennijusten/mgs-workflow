process FASTQC {
    label "FASTQC"
    cpus "${params.cpus}"
    memory "${params.mem}"
    input:
        path(reads)
    output:
        path("*.html"), emit: html
        path("*.zip"), emit: zip
    shell:
        '''
        fastqc -t !{params.cpus} !{reads}
        '''
}
