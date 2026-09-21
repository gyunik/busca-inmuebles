import React, { useState, useMemo } from 'react';
import { Search, X, Check, MapPin, ChevronDown, ChevronUp } from 'lucide-react';
import { LocationCatalog } from '../types/property';

interface MultiSelectNeighborhoodsProps {
  catalog: LocationCatalog;
  selectedNeighborhoods: string[];
  onChange: (neighborhoods: string[]) => void;
}

export const MultiSelectNeighborhoods: React.FC<MultiSelectNeighborhoodsProps> = ({
  catalog,
  selectedNeighborhoods,
  onChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeZone, setActiveZone] = useState<string>('CABA');

  const zones = Object.keys(catalog);

  const filteredCatalog = useMemo(() => {
    if (!searchTerm.trim()) return catalog;
    const lower = searchTerm.toLowerCase();
    const result: LocationCatalog = {};
    for (const [zone, list] of Object.entries(catalog)) {
      const matched = list.filter((n) => n.toLowerCase().includes(lower));
      if (matched.length > 0) {
        result[zone] = matched;
      }
    }
    return result;
  }, [catalog, searchTerm]);

  const toggleNeighborhood = (neigh: string) => {
    if (selectedNeighborhoods.includes(neigh)) {
      onChange(selectedNeighborhoods.filter((n) => n !== neigh));
    } else {
      onChange([...selectedNeighborhoods, neigh]);
    }
  };

  const removeNeighborhood = (neigh: string) => {
    onChange(selectedNeighborhoods.filter((n) => n !== neigh));
  };

  const selectAllInZone = (zone: string) => {
    const list = catalog[zone] || [];
    const newSelected = Array.from(new Set([...selectedNeighborhoods, ...list]));
    onChange(newSelected);
  };

  const deselectAllInZone = (zone: string) => {
    const list = catalog[zone] || [];
    const listSet = new Set(list);
    onChange(selectedNeighborhoods.filter((n) => !listSet.has(n)));
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1">
          <MapPin className="w-3.5 h-3.5 text-blue-600" />
          Barrios y Localidades
        </label>
        {selectedNeighborhoods.length > 0 && (
          <button
            onClick={() => onChange([])}
            className="text-[11px] text-blue-600 hover:text-blue-800 font-medium"
          >
            Limpiar ({selectedNeighborhoods.length})
          </button>
        )}
      </div>

      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-white border border-gray-300 rounded-md px-3 py-2 text-left text-sm flex items-center justify-between shadow-xs hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="truncate text-gray-700">
          {selectedNeighborhoods.length === 0 ? (
            <span className="text-gray-400">Seleccionar barrios...</span>
          ) : (
            <span className="font-semibold text-gray-900">
              {selectedNeighborhoods.length} {selectedNeighborhoods.length === 1 ? 'barrio seleccionado' : 'barrios seleccionados'}
            </span>
          )}
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>

      {/* Selected Tags Chips */}
      {selectedNeighborhoods.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2 max-h-24 overflow-y-auto p-1 bg-gray-50 rounded border border-gray-200">
          {selectedNeighborhoods.map((n) => (
            <span
              key={n}
              className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full border border-blue-200 font-medium"
            >
              {n}
              <button
                type="button"
                onClick={() => removeNeighborhood(n)}
                className="hover:text-blue-900 focus:outline-none"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Dropdown / Modal Content */}
      {isOpen && (
        <div className="mt-2 p-3 bg-white border border-gray-200 rounded-lg shadow-lg">
          {/* Search Box */}
          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar barrio (ej. Palermo, Belgrano, Olivos)..."
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Zone Tabs */}
          {!searchTerm && (
            <div className="flex border-b border-gray-200 mb-2 overflow-x-auto text-[11px]">
              {zones.map((zone) => {
                const countInZone = (catalog[zone] || []).filter((n) => selectedNeighborhoods.includes(n)).length;
                return (
                  <button
                    key={zone}
                    type="button"
                    onClick={() => setActiveZone(zone)}
                    className={`px-2.5 py-1 font-semibold whitespace-nowrap border-b-2 transition-colors ${
                      activeZone === zone
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {zone} {countInZone > 0 && `(${countInZone})`}
                  </button>
                );
              })}
            </div>
          )}

          {/* Quick Actions for active zone */}
          {!searchTerm && (
            <div className="flex justify-between items-center text-[10px] text-gray-500 mb-2 px-1">
              <span>{catalog[activeZone]?.length || 0} opciones</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => selectAllInZone(activeZone)}
                  className="text-blue-600 hover:underline"
                >
                  Seleccionar todos
                </button>
                <span>·</span>
                <button
                  type="button"
                  onClick={() => deselectAllInZone(activeZone)}
                  className="text-gray-500 hover:underline"
                >
                  Deseleccionar
                </button>
              </div>
            </div>
          )}

          {/* Neighborhoods List */}
          <div className="max-h-48 overflow-y-auto space-y-1 text-xs pr-1">
            {searchTerm ? (
              Object.keys(filteredCatalog).length === 0 ? (
                <p className="text-center py-4 text-gray-400 text-xs">No se encontraron barrios</p>
              ) : (
                Object.entries(filteredCatalog).map(([zone, list]) => (
                  <div key={zone} className="mb-2">
                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">{zone}</div>
                    <div className="grid grid-cols-2 gap-1">
                      {list.map((n) => {
                        const checked = selectedNeighborhoods.includes(n);
                        return (
                          <label
                            key={n}
                            className={`flex items-center gap-1.5 p-1 rounded cursor-pointer transition-colors ${
                              checked ? 'bg-blue-50 text-blue-800 font-medium' : 'hover:bg-gray-50 text-gray-700'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleNeighborhood(n)}
                              className="rounded text-blue-600 focus:ring-0 w-3.5 h-3.5"
                            />
                            <span className="truncate">{n}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))
              )
            ) : (
              <div className="grid grid-cols-2 gap-1">
                {(catalog[activeZone] || []).map((n) => {
                  const checked = selectedNeighborhoods.includes(n);
                  return (
                    <label
                      key={n}
                      className={`flex items-center gap-1.5 p-1 rounded cursor-pointer transition-colors ${
                        checked ? 'bg-blue-50 text-blue-800 font-medium' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleNeighborhood(n)}
                        className="rounded text-blue-600 focus:ring-0 w-3.5 h-3.5"
                      />
                      <span className="truncate">{n}</span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>

          {/* Close button */}
          <div className="mt-2 pt-2 border-t border-gray-100 flex justify-end">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1 rounded"
            >
              Listo
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
