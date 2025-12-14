import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardMedia,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Typography,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Image as ImageIcon,
  VideoLibrary as VideoIcon,
  AudioFile as AudioIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface MediaItem {
  id: string;
  identifier: string;
  type: 'image' | 'video' | 'audio';
  status: string;
  content_type: string;
  content_title?: string;
  subject_id: string;
  created_datetime: string;
  file_size: number;
  width?: number;
  height?: number;
  download_url: string;
  thumbnail_url?: string;
}

interface MediaViewerProps {
  patientId: string;
  onClose?: () => void;
}

const MediaViewer: React.FC<MediaViewerProps> = ({ patientId, onClose }) => {
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMedia, setSelectedMedia] = useState<MediaItem | null>(null);
  const [zoom, setZoom] = useState(1);
  const [filterType, setFilterType] = useState<'all' | 'image' | 'video' | 'audio'>('all');

  useEffect(() => {
    fetchMedia();
  }, [patientId, filterType]);

  const fetchMedia = async () => {
    try {
      setLoading(true);
      const typeParam = filterType !== 'all' ? `&type=${filterType}` : '';
      const response = await axios.get(
        `/api/v1/media/patient/${patientId}/?${typeParam}`
      );
      setMediaItems(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching media:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMediaClick = (media: MediaItem) => {
    setSelectedMedia(media);
    setZoom(1);
  };

  const handleClose = () => {
    setSelectedMedia(null);
    setZoom(1);
  };

  const handleDownload = async (media: MediaItem) => {
    try {
      const response = await axios.get(media.download_url, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', media.content_title || media.identifier);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading media:', error);
    }
  };

  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <ImageIcon />;
      case 'video':
        return <VideoIcon />;
      case 'audio':
        return <AudioIcon />;
      default:
        return <ImageIcon />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Filters */}
      <Box mb={2} display="flex" gap={1}>
        <Chip
          label="Todos"
          onClick={() => setFilterType('all')}
          color={filterType === 'all' ? 'primary' : 'default'}
        />
        <Chip
          icon={<ImageIcon />}
          label="Imagens"
          onClick={() => setFilterType('image')}
          color={filterType === 'image' ? 'primary' : 'default'}
        />
        <Chip
          icon={<VideoIcon />}
          label="Vídeos"
          onClick={() => setFilterType('video')}
          color={filterType === 'video' ? 'primary' : 'default'}
        />
        <Chip
          icon={<AudioIcon />}
          label="Áudios"
          onClick={() => setFilterType('audio')}
          color={filterType === 'audio' ? 'primary' : 'default'}
        />
      </Box>

      {/* Media Grid */}
      <ImageList cols={4} gap={8}>
        {mediaItems.map((media) => (
          <ImageListItem key={media.id} onClick={() => handleMediaClick(media)} sx={{ cursor: 'pointer' }}>
            {media.type === 'image' && media.thumbnail_url ? (
              <img
                src={media.thumbnail_url}
                alt={media.content_title || media.identifier}
                loading="lazy"
                style={{ height: 200, objectFit: 'cover' }}
              />
            ) : (
              <Box
                sx={{
                  height: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'grey.200',
                }}
              >
                {getMediaIcon(media.type)}
              </Box>
            )}
            <ImageListItemBar
              title={media.content_title || media.identifier}
              subtitle={`${formatDate(media.created_datetime)} • ${formatFileSize(media.file_size)}`}
              actionIcon={
                <IconButton
                  sx={{ color: 'white' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownload(media);
                  }}
                >
                  <DownloadIcon />
                </IconButton>
              }
            />
          </ImageListItem>
        ))}
      </ImageList>

      {/* Media Dialog */}
      <Dialog
        open={Boolean(selectedMedia)}
        onClose={handleClose}
        maxWidth="lg"
        fullWidth
      >
        {selectedMedia && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">
                  {selectedMedia.content_title || selectedMedia.identifier}
                </Typography>
                <Box>
                  {selectedMedia.type === 'image' && (
                    <>
                      <IconButton onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}>
                        <ZoomOutIcon />
                      </IconButton>
                      <IconButton onClick={() => setZoom(Math.min(3, zoom + 0.25))}>
                        <ZoomInIcon />
                      </IconButton>
                    </>
                  )}
                  <IconButton onClick={() => handleDownload(selectedMedia)}>
                    <DownloadIcon />
                  </IconButton>
                  <IconButton onClick={handleClose}>
                    <CloseIcon />
                  </IconButton>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box textAlign="center">
                {selectedMedia.type === 'image' && (
                  <img
                    src={`/api/v1/media/${selectedMedia.id}/preview/`}
                    alt={selectedMedia.content_title || ''}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '70vh',
                      transform: `scale(${zoom})`,
                      transition: 'transform 0.2s',
                    }}
                  />
                )}
                {selectedMedia.type === 'video' && (
                  <video
                    controls
                    style={{ maxWidth: '100%', maxHeight: '70vh' }}
                    src={selectedMedia.download_url}
                  />
                )}
                {selectedMedia.type === 'audio' && (
                  <audio controls style={{ width: '100%' }} src={selectedMedia.download_url} />
                )}
              </Box>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  <strong>Data:</strong> {formatDate(selectedMedia.created_datetime)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  <strong>Tamanho:</strong> {formatFileSize(selectedMedia.file_size)}
                </Typography>
                {selectedMedia.width && selectedMedia.height && (
                  <Typography variant="body2" color="textSecondary">
                    <strong>Dimensões:</strong> {selectedMedia.width} x {selectedMedia.height}px
                  </Typography>
                )}
                <Typography variant="body2" color="textSecondary">
                  <strong>Tipo:</strong> {selectedMedia.content_type}
                </Typography>
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>

      {mediaItems.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="textSecondary">
            Nenhuma mídia encontrada
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default MediaViewer;
