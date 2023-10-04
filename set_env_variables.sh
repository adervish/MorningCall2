 yq e '.env_variables | to_entries | .[] | "export " + .key + "=" + .value' secrets.yaml
