"""Development-only fixed accounts. Passwords are stored as Argon2id hashes only.

The demo passwords used before this file was hardened remain unchanged; only their
stored representation changed from plaintext to salted Argon2id hashes.
"""
ADMIN_CREDENTIALS = {
    "email": "admin@iitdh.ac.in",
    "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$qJewvHLeu741iwwCTxx22A$/axSDBoCRwbVCnkKdFFuNhcnCcN6fDZhEjTk//bNm84",
    "name": "HostelFix Administrator",
}
STAFF_CREDENTIALS = [
    {"email":"maintenance-staff1@iitdh.ac.in","password_hash":"$argon2id$v=19$m=65536,t=3,p=4$q4lJJ8eEjywflFCJ3jDxiA$Ewtx/PbohKrh3aVvqvBwBVNC5NemQgEBGAiL621tQXA","name":"Maintenance Staff 1","category":"Maintenance"},
    {"email":"maintenance-staff2@iitdh.ac.in","password_hash":"$argon2id$v=19$m=65536,t=3,p=4$AXI9X+gKRVoJickJiPmY5A$nk4yNxX5NXppIFeQVDegMBpr2LOzubM9npFxzkIetNs","name":"Maintenance Staff 2","category":"Maintenance"},
    {"email":"housekeeping-staff1@iitdh.ac.in","password_hash":"$argon2id$v=19$m=65536,t=3,p=4$NL9F2u+uAaNk5WZ4isHHgQ$wt92w8s7xNp9RODPXPioVA+zgHPkIY/8i/ZQb3jB8VI","name":"Housekeeping Staff 1","category":"Housekeeping"},
    {"email":"housekeeping-staff2@iitdh.ac.in","password_hash":"$argon2id$v=19$m=65536,t=3,p=4$R0/pOBfj7FCKF87fzwXkVg$8WphkXCNmKyunw7k0fm0SvyOAMcjFDPz353TQixLY6M","name":"Housekeeping Staff 2","category":"Housekeeping"},
]
