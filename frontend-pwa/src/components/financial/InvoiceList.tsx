import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText } from 'lucide-react';

interface Invoice {
    resourceType: string;
    id: string;
    status: string;
    totalGross?: {
        value: number;
        currency: string;
    };
    date?: string;
}

const InvoiceList: React.FC = () => {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInvoices = async () => {
            try {
                const response = await axios.get('/financial/invoices/');
                console.log("Invoice API Response:", response.data);

                if (Array.isArray(response.data)) {
                    setInvoices(response.data);
                    // Clear error if success
                } else {
                    console.error("Expected array from API, got:", response.data);
                    setInvoices([]);
                }
            } catch (error) {
                console.error("Failed to fetch invoices", error);
                setInvoices([]);
            } finally {
                setLoading(false);
            }
        };
        fetchInvoices();
    }, []);

    if (loading) return <div className="p-4 text-center">Carregando faturas...</div>;

    if (!Array.isArray(invoices) || invoices.length === 0) {
        return (
            <div className="text-center p-8 bg-gray-50 rounded-lg">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                    {Array.isArray(invoices) ? "Nenhuma fatura encontrada" : "Erro ao carregar faturas"}
                </h3>
            </div>
        );
    }

    return (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
                {invoices.map((invoice) => (
                    <li key={invoice.id}>
                        <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium text-indigo-600 truncate">
                                    Fatura #{invoice.id}
                                </p>
                                <div className="ml-2 flex-shrink-0 flex">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${invoice.status === 'issued' ? 'bg-yellow-100 text-yellow-800' :
                                        invoice.status === 'balanced' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                        }`}>
                                        {invoice.status}
                                    </span>
                                </div>
                            </div>
                            <div className="mt-2 sm:flex sm:justify-between">
                                <div className="sm:flex">
                                    <p className="flex items-center text-sm text-gray-500">
                                        Valor: {invoice.totalGross?.value?.toFixed(2)} {invoice.totalGross?.currency}
                                    </p>
                                </div>
                                <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                                    <p>
                                        Emitido em: {invoice.date ? new Date(invoice.date).toLocaleDateString() : 'N/A'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default InvoiceList;
