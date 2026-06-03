param(
    [string]$Repo = "dobrerares/brewlog",
    [string]$Environment = "production",
    [string]$BackendService = "backend",
    [string]$FrontendService = "frontend",
    [string]$PostgresService = "Postgres",
    [string]$MongoService = "MongoDB",
    [string]$FrontendDomain = "",
    [string]$BackendDomain = "",
    [string]$AdminEmail = "",
    [switch]$SkipCreateServices
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Railway {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    Write-Host "railway $($Args -join ' ')"
    & railway @Args
}

function New-Secret {
    $bytes = [byte[]]::new(48)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes)
}

function Read-PlainSecret {
    param([string]$Prompt)
    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Set-RailwayVariables {
    param(
        [string]$Service,
        [hashtable]$Variables
    )

    foreach ($key in $Variables.Keys) {
        $value = [string]$Variables[$key]
        if ($value.Length -eq 0) {
            continue
        }
        Invoke-Railway variable set "$key=$value" --service $Service --environment $Environment --skip-deploys
    }
}

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    throw "Railway CLI is not installed or not on PATH. Install it, then run 'railway login'."
}

Invoke-Railway whoami | Out-Host

if (-not $SkipCreateServices) {
    Invoke-Railway add --database postgres --service $PostgresService
    Invoke-Railway add --database mongo --service $MongoService
    Invoke-Railway add --repo $Repo --service $BackendService
    Invoke-Railway add --repo $Repo --service $FrontendService
}

if (-not $AdminEmail) {
    $AdminEmail = Read-Host -Prompt "Admin bootstrap email"
}

$AdminPassword = Read-PlainSecret "Admin bootstrap password"
$SessionSecret = New-Secret
$JwtSecret = New-Secret

$backendVars = @{
    DATABASE_URL = '${{' + $PostgresService + '.DATABASE_URL}}'
    MONGO_URL = '${{' + $MongoService + '.MONGO_URL}}'
    MONGO_DB = "brewlog_chat"
    SESSION_SECRET = $SessionSecret
    JWT_SECRET = $JwtSecret
    AUTH_COOKIE_SECURE = "true"
    AUTH_COOKIE_SAMESITE = "none"
    ALLOW_DEV_MAGIC_LINK = "false"
    ALLOW_DEV_TOTP_CODE = "false"
    ADMIN_BOOTSTRAP_EMAIL = $AdminEmail
    ADMIN_BOOTSTRAP_PASSWORD = $AdminPassword
    RESEND_API_KEY = $env:RESEND_API_KEY
    RESEND_FROM_EMAIL = $(if ($env:RESEND_FROM_EMAIL) { $env:RESEND_FROM_EMAIL } else { "BrewLog <onboarding@resend.dev>" })
}

if ($FrontendDomain) {
    $backendVars.CORS_ORIGINS = $FrontendDomain.TrimEnd("/")
    $backendVars.APP_BASE_URL = $FrontendDomain.TrimEnd("/")
}

Set-RailwayVariables -Service $BackendService -Variables $backendVars

if ($BackendDomain) {
    Set-RailwayVariables -Service $FrontendService -Variables @{
        VITE_API_BASE = $BackendDomain.TrimEnd("/")
    }
}

Write-Host ""
Write-Host "Next one-time Railway dashboard settings:"
Write-Host "1. Backend service Source root directory: /backend"
Write-Host "2. Backend service config path: /backend/railway.json"
Write-Host "3. Frontend service Source root directory: /brewlog"
Write-Host "4. Frontend service config path: /brewlog/railway.json"
Write-Host "5. Create public domains for backend and frontend."
Write-Host "6. Re-run this script with -BackendDomain and -FrontendDomain, or set:"
Write-Host "   backend: CORS_ORIGINS, APP_BASE_URL"
Write-Host "   frontend: VITE_API_BASE"
Write-Host "7. Redeploy both app services."
