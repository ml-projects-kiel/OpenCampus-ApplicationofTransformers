#!/bin/bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.31.3


# Create report file for upload
vulneravility=$(trivy fs "poetry.lock" --format template --template "@trivy.tpl" -o 'trivy_report.json')

# Load report file for CLI report
foundvul=$(jq -r '.issues' < 'trivy_report.json')
if [ -z "$(jq -r '.[]' <<< $foundvul)" ]; then
    echo "No vulnerabilities found."
else
    echo "Vulnerabilities found:"
    printf "%20s%20s%20s%20s\t%s\n" 'Package' 'InstalledVersion' 'FixedVersion' 'Severity' 'Title'
    for row in $(echo "${foundvul}" | jq -r '.[] | @base64'); do
        _jq() {
            echo ${row} | base64 --decode | jq -r ${1}
        }
        printf "%20s%20s%20s%20s\t$(_jq '.primaryLocation.message')\n" $(_jq '.packageName') $(_jq '.packageVersion') $(_jq '.fixedVersion') $(_jq '.severity')
    done
    exit 1
fi
