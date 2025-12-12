/**
 * Sprint 26: API Service for Appointments
 * 
 * Handles appointment-related API calls
 */

import api from './api';

export interface Appointment {
    id: string;
    practitioner: {
        id: string;
        name: string;
        specialty: string;
        crm?: string;
    };
    patient: {
        id: string;
        name: string;
    };
    date: string;
    startTime: string;
    endTime: string;
    status: 'proposed' | 'pending' | 'booked' | 'arrived' | 'fulfilled' | 'cancelled' | 'noshow';
    appointmentType: 'routine' | 'walkin' | 'checkup' | 'followup' | 'emergency';
    serviceType: 'in-person' | 'telemedicine';
    location?: {
        name: string;
        address: string;
        room?: string;
    };
    reason?: string;
    notes?: string;
    meetingUrl?: string;
    createdAt: string;
    updatedAt: string;
}

export interface CreateAppointmentRequest {
    practitionerId: string;
    date: string;
    startTime: string;
    serviceType: 'in-person' | 'telemedicine';
    reason?: string;
}

export interface TimeSlot {
    time: string;
    available: boolean;
    practitionerId?: string;
}

export interface AvailableSlotsRequest {
    practitionerId: string;
    date: string;
}

class AppointmentsService {
    /**
     * Get all appointments for the current patient
     */
    async getAppointments(params?: {
        status?: string;
        from?: string;
        to?: string;
        limit?: number;
    }): Promise<Appointment[]> {
        try {
            const response = await api.get<{ appointments: Appointment[] }>('/patient/appointments', {
                params,
            });
            return response.data.appointments;
        } catch (error) {
            console.error('Error fetching appointments:', error);
            throw error;
        }
    }

    /**
     * Get a single appointment by ID
     */
    async getAppointment(id: string): Promise<Appointment> {
        try {
            const response = await api.get<Appointment>(`/appointments/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching appointment:', error);
            throw error;
        }
    }

    /**
     * Get available time slots for a practitioner on a specific date
     */
    async getAvailableSlots(request: AvailableSlotsRequest): Promise<TimeSlot[]> {
        try {
            const response = await api.get<{ slots: TimeSlot[] }>('/appointments/slots', {
                params: request,
            });
            return response.data.slots;
        } catch (error) {
            console.error('Error fetching available slots:', error);
            throw error;
        }
    }

    /**
     * Create a new appointment
     */
    async createAppointment(data: CreateAppointmentRequest): Promise<Appointment> {
        try {
            const response = await api.post<Appointment>('/appointments', data);
            return response.data;
        } catch (error) {
            console.error('Error creating appointment:', error);
            throw error;
        }
    }

    /**
     * Cancel an appointment
     */
    async cancelAppointment(id: string, reason?: string): Promise<void> {
        try {
            await api.patch(`/appointments/${id}/cancel`, { reason });
        } catch (error) {
            console.error('Error cancelling appointment:', error);
            throw error;
        }
    }

    /**
     * Reschedule an appointment
     */
    async rescheduleAppointment(
        id: string,
        newDate: string,
        newTime: string
    ): Promise<Appointment> {
        try {
            const response = await api.patch<Appointment>(`/appointments/${id}/reschedule`, {
                date: newDate,
                startTime: newTime,
            });
            return response.data;
        } catch (error) {
            console.error('Error rescheduling appointment:', error);
            throw error;
        }
    }

    /**
     * Confirm attendance for an appointment
     */
    async confirmAppointment(id: string): Promise<void> {
        try {
            await api.patch(`/appointments/${id}/confirm`);
        } catch (error) {
            console.error('Error confirming appointment:', error);
            throw error;
        }
    }

    /**
     * Get upcoming appointments count
     */
    async getUpcomingCount(): Promise<number> {
        try {
            const response = await api.get<{ count: number }>('/patient/appointments/upcoming-count');
            return response.data.count;
        } catch (error) {
            console.error('Error fetching upcoming count:', error);
            return 0;
        }
    }
}

export const appointmentsService = new AppointmentsService();
export default appointmentsService;
