import { useEffect, useCallback } from 'react';
import Particles from 'react-tsparticles';
import { loadFull } from 'tsparticles';

const ParticlesBackground = ({ particleColor = '#ffffff' }) => {
  const particlesInit = useCallback(async (engine) => {
    await loadFull(engine);
  }, []);

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={{
        background: { color: { value: 'transparent' } },
        particles: {
          number: { value: 50 },
          color: { value: particleColor },
          opacity: { value: 0.5 },
          size: { value: 3 },
          move: {
            enable: true,
            speed: 1,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false,
          },
          line_linked: {
            enable: true,
            distance: 150,
            color: particleColor,
            opacity: 0.4,
            width: 1
          },
        },
        interactivity: {
          events: {
            onhover: { enable: true, mode: 'repulse' }
          }
        }
      }}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%'
      }}
    />
  );
};

export default ParticlesBackground;