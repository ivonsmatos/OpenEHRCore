import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { CreditCard } from 'lucide-react';

interface Coverage {
    resourceType: string;
    id: string;
    status: string;
    subscriberId?: string;
    payor?: Array<{ display?: string }>;
    type?: { text?: string };
}

const CoverageList: React.FC = () => {
    const [coverages, setCoverages] = useState<Coverage[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCoverage = async () => {
            try {
                const response = await axios.get('/financial/coverage/');
                if (Array.isArray(response.data)) {
                    setCoverages(response.data);
                } else {
                    console.error("Coverage API returned non-array:", response.data);
                    setCoverages([]);
                }
            } catch (error) {
                console.error("Failed to fetch coverage", error);
                setCoverages([]);
            } finally {
                setLoading(false);
            }
        };
        fetchCoverage();
    }, []);

    if (loading) return <div className="p-4 text-center">Carregando convênios...</div>;

    if (coverages.length === 0) {
        return (
            <div className="text-center p-8 bg-gray-50 rounded-lg">
                <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum convênio encontrado</h3>
            </div>
        );
    }

    return (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
                {coverages.map((cov) => (
                    <li key={cov.id}>
                        <div className="px-4 py-4 sm:px-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg leading-6 font-medium text-gray-900">
                                    {cov.payor?.[0]?.display || "Convênio Desconhecido"}
                                </h3>
                                <p className="text-sm text-gray-500">
                                    Status: <span className="font-semibold text-green-600">{cov.status}</span>
                                </p>
                            </div>
                            <div className="mt-2 max-w-xl text-sm text-gray-500">
                                <p>Carterinha: {cov.subscriberId}</p>
                                <p>Tipo: {cov.type?.text}</p>
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default CoverageList;
