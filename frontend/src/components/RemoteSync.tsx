import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

export default function RemoteSync() {
  const navigate = useNavigate();
  const lastEventId = useRef(0);

  useEffect(() => {
    const poll = async () => {
      try {
        const resp = await api.get(`/remote/events?since_id=${lastEventId.current}`);
        const newEvents = resp.data;
        
        if (newEvents.length > 0) {
          lastEventId.current = newEvents[newEvents.length - 1].id;
          
          for (const event of newEvents) {
            handleEvent(event);
          }
        }
      } catch (err) {
        // Silently fail polling errors
      }
    };

    const handleEvent = (event: any) => {
      console.log("Remote Event Received:", event);
      
      switch (event.event_type) {
        case 'NAVIGATE':
          if (event.payload?.to) {
             const path = event.payload.to === 'dashboard' ? '/' : `/${event.payload.to}`;
             navigate(path);
          }
          break;
        case 'ATTACK_SIMULATION':
          // Trigger a fake notification and navigate to alerts
          navigate('/alerts');
          break;
        case 'PANIC_LOCK':
          document.body.innerHTML = `
            <div style="background: black; color: red; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; text-align: center; padding: 20px;">
              <h1 style="font-size: 4rem; margin-bottom: 20px;">🚨 SYSTEM LOCKED 🚨</h1>
              <p style="font-size: 1.5rem; letter-spacing: 0.2em;">CRITICAL BREACH DETECTED — EMERGENCY PROTOCOL ACTIVE</p>
              <p style="margin-top: 40px; color: #555;">ADMIN LOCKDOWN INITIATED VIA MOBILE COMMAND</p>
            </div>
          `;
          break;
      }
    };

    const interval = setInterval(poll, 1500);
    return () => clearInterval(interval);
  }, [navigate]);

  return null;
}
