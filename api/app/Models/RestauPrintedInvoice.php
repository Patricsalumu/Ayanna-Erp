<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class RestauPrintedInvoice extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'restau_printed_invoices';
    protected $fillable = ['id', 'panier_id', 'user_id', 'printed_at', 'montant_total', 'montant_paye', 'note'];
    protected $casts = ['montant_total' => 'decimal:2', 'montant_paye' => 'decimal:2', 'printed_at' => 'datetime'];

    public function panier() { return $this->belongsTo(RestauPanier::class, 'panier_id'); }
    public function user()   { return $this->belongsTo(User::class, 'user_id'); }
}
