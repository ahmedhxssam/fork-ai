import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import Studio from './studio/Studio';
const logistics=new URLSearchParams(window.location.search).get('view')==='logistics';
if(logistics) void import('./styles.css');
createRoot(document.getElementById('root')!).render(<React.StrictMode>{logistics?<App/>:<Studio/>}</React.StrictMode>);
