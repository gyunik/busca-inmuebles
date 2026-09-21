import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Layers, CheckCircle2, AlertCircle, Clock, Play } from 'lucide-react';
import axios from 'axios';
import { ScrapeJob } from '../types/property';

interface ScrapeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScrapeCompleted: () => void;
}

export const ScrapeModal: React.FC<ScrapeModalProps> = ({
  isOpen,
  onClose,
  onScrapeCompleted
}) => {
  const [portal, setPortal] = useState<string>('all');
  const [propertyType, setPropertyType] = useState<string>('all');
  const [zone, setZone] = useState<string>('all');
  const [isStarting, setIsStarting] = useState(false);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/scrape/jobs');
      setJobs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchJobs();
      const interval = setInterval(fetchJobs, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleStartScrape = async () => {
    setIsStarting(true);
    setMessage(null);
    try {
      await axios.post('http://127.0.0.1:8000/api/scrape/start', {
        portal: portal,
        property_type: propertyType === 'all' ? null : propertyType,
        zone: zone === 'all' ? null : zone
      });
      setMessage('Escaneo iniciado en segundo plano. La lista se actualizará automáticamente.');
      fetchJobs();
      setTimeout(onScrapeCompleted, 2000);
    } catch (err) {
      setMessage('Error al iniciar el escaneo.');
    } finally {
      setIsStarting(false);
    }
  };

  const handleRunDeduplication = async () => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/scrape/deduplicate');
      setMessage(res.data.message);
      onScrapeCompleted();
    } catch (err) {
      setMessage('Error al ejecutar la deduplicación.');
    }
  };

  const handleLoadSeed = async () => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/scrape/seed');
      setMessage(res.data.message);
      onScrapeCompleted();
    } catch (err) {
      setMessage('Error al cargar datos.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-200">
        
        {/* Header */}
        <div className="bg-ml-navy text-white px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-ml-yellow" />
            <h2 className="font-bold text-base">Escanear y Actualizar Portales</h2>
          </div>
          <button onClick={onClose} className="text-gray-300 hover:text-white p-1 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          
          {message && (
            <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-blue-600" />
              <span>{message}</span>
            </div>
          )}

          {/* Form Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            
            {/* Portal */}
            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Portal</label>
              <select
                value={portal}
                onChange={(e) => setPortal(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded p-2 focus:ring-1 focus:ring-blue-500"
              >
                <option value="all">Todos los Portales</option>
                <option value="mercadolibre">Mercado Libre</option>
                <option value="zonaprop">Zonaprop</option>
                <option value="argenprop">Argenprop</option>
                <option value="properati">Properati</option>
              </select>
            </div>

            {/* Property Type */}
            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Tipo de Inmueble</label>
              <select
                value={propertyType}
                onChange={(e) => setPropertyType(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded p-2 focus:ring-1 focus:ring-blue-500"
              >
                <option value="all">Todos los Tipos</option>
                <option value="departamento">Departamentos</option>
                <option value="casa">Casas</option>
                <option value="ph">PH</option>
              </select>
            </div>

            {/* Zone */}
            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Zona</label>
              <select
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded p-2 focus:ring-1 focus:ring-blue-500"
              >
                <option value="all">Todas las Zonas</option>
                <option value="CABA">CABA</option>
                <option value="GBA Norte">GBA Norte</option>
                <option value="GBA Sur">GBA Sur</option>
                <option value="GBA Oeste">GBA Oeste</option>
              </select>
            </div>

          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2 pt-2">
            <button
              onClick={handleStartScrape}
              disabled={isStarting}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-lg text-xs flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>{isStarting ? 'Iniciando...' : 'Iniciar Escaneo Ahora'}</span>
            </button>

            <button
              onClick={handleRunDeduplication}
              className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2.5 px-3 rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-sm transition-all"
              title="Detectar duplicados entre portales"
            >
              <Layers className="w-4 h-4" />
              <span>Detectar Duplicados</span>
            </button>
          </div>

          {/* Recent Jobs History */}
          <div className="pt-3 border-t border-gray-200">
            <h4 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-gray-500" />
              Historial de Escaneos Recientes
            </h4>
            
            <div className="max-h-36 overflow-y-auto space-y-1.5 text-xs">
              {jobs.length === 0 ? (
                <p className="text-gray-400 text-center py-2 text-xs">No hay escaneos registrados aún</p>
              ) : (
                jobs.map((j) => (
                  <div key={j.id} className="p-2 bg-gray-50 rounded border border-gray-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-gray-800 capitalize">{j.portal}</span>
                      <span className="text-gray-500 text-[11px] ml-2">
                        {j.message || j.status}
                      </span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      j.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : j.status === 'running'
                        ? 'bg-blue-100 text-blue-800 animate-pulse'
                        : j.status === 'failed'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-gray-200 text-gray-800'
                    }`}>
                      {j.status === 'completed' ? '✓ Listo' : j.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-5 py-3 border-t border-gray-200 flex justify-between items-center">
          <button
            onClick={handleLoadSeed}
            className="text-xs text-gray-500 hover:text-gray-800 hover:underline"
          >
            Recargar datos de prueba
          </button>
          <button
            onClick={onClose}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-4 py-1.5 rounded text-xs"
          >
            Cerrar
          </button>
        </div>

      </div>
    </div>
  );
};
