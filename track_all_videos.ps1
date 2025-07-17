$videos = Get-ChildItem "for_tracking\*" -Include *.mp4, *.mkv

foreach ($video in $videos) {
    Write-Host "Processing: $($video.Name)" -ForegroundColor Cyan

    sleap-track `
        -m "SLEAP_track\models\250702_114533.centroid.n=765" `
        -m "SLEAP_track\models\250702_132640.centered_instance.n=765" `
        --tracking.tracker flow `
        --tracking.similarity centroid `
        --tracking.match hungarian `
        --tracking.max_tracks 2 `
        -n 2 `
        -o "tracked_videos" `
        $video.FullName
}
