import React, { useEffect, useRef } from 'react';

export default function LiveBackground({ weatherCode, isDay }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Determine basic animation states based on WMO Weather Codes
    const isRain = [51, 53, 55, 61, 63, 65, 80, 81, 82].includes(weatherCode);
    const isSnow = [71, 73, 75, 77, 85, 86].includes(weatherCode);
    const isThunder = [95, 96, 99].includes(weatherCode);
    const isCloudy = [1, 2, 3].includes(weatherCode);

    // Particles system
    const particles = [];
    const maxParticles = isRain ? 120 : isSnow ? 80 : 0;

    for (let i = 0; i < maxParticles; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        speed: isRain ? 10 + Math.random() * 10 : 1 + Math.random() * 3,
        radius: isRain ? 1 : 2 + Math.random() * 3,
        opacity: Math.random() * 0.5 + 0.2
      });
    }

    let lightningFlash = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Handle Thunderstorm Flash
      if (isThunder && Math.random() > 0.98) {
        lightningFlash = 10;
      }

      if (lightningFlash > 0) {
        ctx.fillStyle = `rgba(255, 255, 255, ${lightningFlash / 10 * 0.25})`;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        lightningFlash--;
      }

      // Render Dynamic Weather Particles
      ctx.fillStyle = isRain ? 'rgba(156, 163, 175, 0.6)' : 'rgba(255, 255, 255, 0.8)';
      for (let i = 0; i < particles.length; i++) {
        let p = particles[i];
        ctx.beginPath();
        if (isRain) {
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x + 1, p.y + p.speed);
          ctx.strokeStyle = `rgba(147, 197, 253, ${p.opacity})`;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        } else {
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fill();
        }

        p.y += p.speed;
        if (isRain) p.x += 0.5;

        if (p.y > canvas.height) {
          p.y = -10;
          p.x = Math.random() * canvas.width;
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, [weatherCode, isDay]);

  return <canvas ref={canvasRef} className="fixed top-0 left-0 w-full h-full pointer-events-none z-0" />;
}
