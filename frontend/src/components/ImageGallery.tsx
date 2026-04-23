export default function ImageGallery({ images }: { images: string[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      {images.map((image, index) => (
        <div key={index} className="border border-slate-200 rounded-lg overflow-hidden">
          <img
            src={image}
            alt={`Manual diagram ${index + 1}`}
            className="w-full h-auto"
          />
        </div>
      ))}
    </div>
  )
}