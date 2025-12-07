import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Download, Volume2 } from 'lucide-react';

interface AudioPlayerProps {
  src: string;
  autoPlay?: boolean;
}

export function AudioPlayer({ src, autoPlay = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    if (autoPlay && audioRef.current) {
      audioRef.current.play().catch(e => console.log("Autoplay failed", e));
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

  const formatTime = (time: number) => {
    const min = Math.floor(time / 60);
    const sec = Math.floor(time % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full bg-gray-800 rounded-xl p-4 shadow-lg border border-gray-700 mt-4">
      <audio 
        ref={audioRef} 
        src={src} 
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMetadata}
        onEnded={onEnded}
      />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-medium text-gray-400">AI Generated Voice</span>
        </div>
        <a 
          href={src} 
          download 
          className="text-gray-400 hover:text-white transition-colors"
          title="Download"
        >
          <Download className="w-4 h-4" />
        </a>
      </div>

      <div className="flex items-center gap-4">
        <button 
          onClick={togglePlay}
          className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center hover:scale-105 transition-transform"
        >
          {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
        </button>

        <div className="flex-1">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden relative">
            <div 
              className="absolute top-0 left-0 h-full bg-blue-500 transition-all duration-100"
              style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

