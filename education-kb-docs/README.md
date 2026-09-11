# Education Knowledge Base Documents

Source documents for the Bedrock Knowledge Base. These are the "Peculiar University" course catalog markdown files that the agent uses to answer student questions.

## Syncing to S3

Upload these documents to your KB docs bucket:

```bash
aws s3 sync ./education-kb-docs/ s3://<account-id>-<region>-education-kb-docs/
```

## Contents

- `index.md` - Top-level catalog index
- `college_of_engineering_index.md` - College of Engineering overview
- `college_of_engineering_AERO_*` - Aerospace Engineering courses
- `college_of_engineering_COMP_*` - Computer Science courses
- `college_of_engineering_DATA_*` - Data Science courses
- `college_of_engineering_ENGI_*` - General Engineering courses
- `college_of_engineering_ENVI_*` - Environmental Engineering courses
