param(
    [Parameter(Mandatory = $true)]
    [string] $DocxPath,

    [Parameter(Mandatory = $true)]
    [string] $OutputPdf,

    [string] $PrinterName = "Microsoft Print to PDF"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$resolvedDocx = (Resolve-Path -LiteralPath $DocxPath).Path
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPdf)
$outputDirectory = Split-Path -Parent $resolvedOutput

if ([System.IO.Path]::GetExtension($resolvedDocx) -ne ".docx") {
    throw "Input must be a .docx file: $resolvedDocx"
}
if ([System.IO.Path]::GetExtension($resolvedOutput) -ne ".pdf") {
    throw "Output must be a .pdf file: $resolvedOutput"
}
if (Test-Path -LiteralPath $resolvedOutput) {
    throw "Refusing to overwrite existing output: $resolvedOutput"
}
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$printer = Get-Printer -Name $PrinterName -ErrorAction Stop
if ($printer.PortName -ne "PORTPROMPT:") {
    throw "Expected a file-output printer on PORTPROMPT:, got $($printer.PortName)"
}

$existingWordIds = @(
    Get-Process WINWORD -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Id
)
$word = $null
$document = $null
$taskWordProcessId = $null
$documentPages = 0

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.ActivePrinter = $PrinterName

    $document = $word.Documents.Open($resolvedDocx, $false, $true)
    $document.Repaginate()
    $documentPages = $document.ComputeStatistics(2)
    $taskWordProcessId = Get-Process WINWORD |
        Where-Object { $_.Id -notin $existingWordIds } |
        Select-Object -First 1 -ExpandProperty Id

    $background = $false
    $append = $false
    $printRange = 0
    $outputName = [string] $resolvedOutput
    $document.PrintOut(
        [ref] $background,
        [ref] $append,
        [ref] $printRange,
        [ref] $outputName
    )

    $lastLength = -1L
    $stablePolls = 0
    for ($poll = 0; $poll -lt 90; $poll++) {
        Start-Sleep -Milliseconds 500
        if (-not (Test-Path -LiteralPath $resolvedOutput)) {
            continue
        }
        $currentLength = (Get-Item -LiteralPath $resolvedOutput).Length
        if ($currentLength -gt 0 -and $currentLength -eq $lastLength) {
            $stablePolls++
        }
        else {
            $stablePolls = 0
        }
        $lastLength = $currentLength
        if ($stablePolls -ge 4) {
            break
        }
    }

    if (-not (Test-Path -LiteralPath $resolvedOutput)) {
        throw "Word print did not create an output file within 45 seconds."
    }
    if ($stablePolls -lt 4) {
        throw "Word print output did not stabilize within 45 seconds."
    }

    # The spooler can retain its exclusive handle after file length stabilizes.
    # A completed print must not fail just because that handle closes late.
    [byte[]] $pdfBytes = @()
    for ($readAttempt = 0; $readAttempt -lt 90; $readAttempt++) {
        try {
            $pdfBytes = [System.IO.File]::ReadAllBytes($resolvedOutput)
            if ($pdfBytes.Length -ge 16) {
                $readTailStart = [Math]::Max(0, $pdfBytes.Length - 1024)
                $readTail = [System.Text.Encoding]::ASCII.GetString($pdfBytes, $readTailStart, $pdfBytes.Length - $readTailStart)
                if ($readTail.Contains("%%EOF")) { break }
            }
        }
        catch [System.IO.IOException] { }
        Start-Sleep -Milliseconds 500
    }
    if ($pdfBytes.Length -lt 16) {
        throw "Word print output is unexpectedly small: $($pdfBytes.Length) bytes"
    }
    $header = [System.Text.Encoding]::ASCII.GetString($pdfBytes, 0, 5)
    $tailStart = [Math]::Max(0, $pdfBytes.Length - 1024)
    $tail = [System.Text.Encoding]::ASCII.GetString(
        $pdfBytes,
        $tailStart,
        $pdfBytes.Length - $tailStart
    )
    if ($header -ne "%PDF-" -or -not $tail.Contains("%%EOF")) {
        throw "Word print output is not a complete PDF file."
    }

    [ordered]@{
        status = "PASS"
        input = $resolvedDocx
        output = $resolvedOutput
        printer = $word.ActivePrinter
        docx_pages = $documentPages
        pdf_bytes = $pdfBytes.Length
    } | ConvertTo-Json -Compress
}
finally {
    $saveChanges = 0
    if ($null -ne $document) {
        try { $document.Close([ref] $saveChanges) } catch {}
    }
    if ($null -ne $word) {
        try { $word.Quit([ref] $saveChanges) } catch {}
    }
    if ($null -ne $document) {
        [void] [Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    if ($null -ne $word) {
        [void] [Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Start-Sleep -Milliseconds 500

    if ($null -ne $taskWordProcessId) {
        $taskWordProcess = Get-Process -Id $taskWordProcessId -ErrorAction SilentlyContinue
        if ($null -ne $taskWordProcess) {
            Stop-Process -Id $taskWordProcessId -Force
        }
    }
}
