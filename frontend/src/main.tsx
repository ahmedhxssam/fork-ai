import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import Studio from './studio/Studio';
const logistics=new URLSearchParams(window.location.search).get('view')==='logistics';
async function renderApp(){
  // The logistics sheet is a separate Vite chunk; mount only after it is ready.
  if(logistics) await import('./styles.css');
  createRoot(document.getElementById('root')!).render(<React.StrictMode>{logistics?<App/>:<Studio/>}</React.StrictMode>);
}
void renderApp();
