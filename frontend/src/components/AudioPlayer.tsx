import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Download, Volume2 } from 'lucide-react';

interface AudioPlayerProps {
  src: string;
  autoPlay?: boolean;
  voiceName?: string;
}

export function AudioPlayer({ src, autoPlay = false, voiceName }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressBarRef = useRef<HTMLDivElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    if (autoPlay && audioRef.current) {
      audioRef.current.play().catch(e => console.log("Autoplay failed", e));
      setIsPlaying(true);
    }
  }, [src, autoPlay]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const onTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const onLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const onEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressBarRef.current) return;
    
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const changePlaybackRate = () => {
    const rates = [1, 1.25, 1.5, 2, 0.75];
    const currentIndex = rates.indexOf(playbackRate);
    const nextIndex = (currentIndex + 1) % rates.length;
    const newRate = rates[nextIndex];
    
    setPlaybackRate(newRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate;
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = src;
    link.download = `${voiceName || 'audio'}_${Date.now()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatTime = (time: number) => {
    const min = Math.floor(time / 60);
    const sec = Math.floor(time % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full bg-gray-800/80 backdrop-blur-sm rounded-2xl p-5 shadow-xl border border-gray-700/50">
      <audio 
        ref={audioRef} 
        src={src} 
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMetadata}
        onEnded={onEnded}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />
      
      {/* Progress Bar and Time - Top */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs font-mono text-gray-400 mb-2">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
        <div 
          ref={progressBarRef}
          onClick={handleProgressClick}
          className="w-full h-3 bg-gray-600 rounded-full overflow-hidden relative cursor-pointer hover:h-3.5 transition-all group border border-gray-500/50"
        >
          <div 
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 via-blue-400 to-purple-500 transition-all duration-100"
            style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
          />
          {/* Hover indicator */}
          <div className="absolute top-0 left-0 w-full h-full opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg ring-2 ring-blue-400"
                 style={{ left: `${(currentTime / (duration || 1)) * 100}%`, marginLeft: '-8px' }}
            />
          </div>
        </div>
      </div>

      {/* Controls - Bottom */}
      <div className="flex items-center justify-between">
        {/* Left: Play Button */}
        <button 
          onClick={togglePlay}
          className="w-11 h-11 rounded-full bg-white text-black flex items-center justify-center hover:scale-105 transition-transform shadow-lg flex-shrink-0"
        >
          {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
        </button>

        {/* Right: Speed and Download */}
        <div className="flex items-center gap-3">
          <button
            onClick={changePlaybackRate}
            className="px-4 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-sm font-semibold text-gray-300 hover:text-white transition-colors"
            title="Change playback speed"
          >
            {playbackRate}x
          </button>

          <button
            onClick={handleDownload}
            className="p-2.5 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
            title="Download audio"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

